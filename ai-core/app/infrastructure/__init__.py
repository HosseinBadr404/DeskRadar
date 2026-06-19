"""
ServiceDesk Radar — AI Infrastructure
app/infrastructure/__init__.py  (Step 17)

Public API (the only three symbols main.py ever imports):
  * initialize_infrastructure() -> InfrastructureHealthStatus
  * run_infrastructure(request) -> InfrastructureResult
  * set_model_for_testing(mock) -> None   (re-exported from embedding_model)

This module is the orchestrator. It owns process-wide state (config, the
embedding model, the seed ticket pool, the knowledge base, the optional Qdrant
adapter) and enforces:

  Startup order (handoff §8):
    1) load config           (fatal -> status="error")
    2) load embedding model  (fail  -> status="degraded", §3.6)
    3) load+validate old_tickets.json -> in-memory TicketVectorEntry pool
    4) load+validate knowledge_articles.json -> build/load article embeddings
    5) optional Qdrant connect + collection ensure + upsert
    6) return InfrastructureHealthStatus

  Per-request order (handoff §7):
    1) build_ticket_text(title, description, category)
    2) encode(text) -> vector
    3) find_similar_tickets(...)
    4) find_related_article(...)
    5) detect_incident_candidate(...)
    6) assemble InfrastructureResult

Contracts:
  * run_infrastructure() NEVER raises (Rule 1); any internal failure is caught
    and returned with the `error` field populated (neutral result otherwise).
  * initialize_infrastructure() never raises; it returns status ok/degraded/error.
  * No analyzer/ import (Rule 5). Thresholds come from config (Rule 4). Python
    cosine fallback is always available; Qdrant is optional (Rule 8).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time

from .embedding_model import (
    EmbeddingModel,
    build_ticket_text,
    set_model_for_testing,  # re-exported as part of the public API
)
from .incident_detector import detect_incident_candidate
from .knowledge_base import KnowledgeBase
from .qdrant_adapter import QdrantAdapter
from .schemas import (
    IncidentCandidate,
    InfrastructureHealthStatus,
    InfrastructureRequest,
    InfrastructureResult,
    OldTicketRecord,
    TicketVectorEntry,
)
from .similarity_search import find_similar_tickets

__all__ = [
    "initialize_infrastructure",
    "run_infrastructure",
    "set_model_for_testing",
]

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG_PATH = "config/infrastructure_config.json"
_DEFAULT_OLD_TICKETS_PATH = "data/old_tickets.json"
_DEFAULT_ARTICLES_PATH = "data/knowledge_articles.json"


# ---------------------------------------------------------------------------- #
# Process-wide state
# ---------------------------------------------------------------------------- #
class _State:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.config: dict = {}
        self.initialized: bool = False
        self.model_ready: bool = False
        self.seed_ticket_pool: list[TicketVectorEntry] = []
        self.seed_title_lookup: dict[int, str] = {}
        self.kb: KnowledgeBase | None = None
        self.qdrant: QdrantAdapter | None = None
        self.startup_latency_ms: float = 0.0
        # cross-request ticket embedding cache (§9.3: never re-embed unless text changes)
        self.ticket_vec_cache: dict[tuple[int, str], list[float]] = {}


_state = _State()


# ---------------------------------------------------------------------------- #
# Startup
# ---------------------------------------------------------------------------- #
def initialize_infrastructure() -> InfrastructureHealthStatus:
    """Run the startup sequence once (called from the FastAPI lifespan). Never raises."""
    t0 = time.perf_counter()
    _state.reset()

    # Step 1 — config (fatal on failure)
    try:
        config = _load_config()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Infrastructure config load failed.")
        return _health_error(f"config_load_failed: {exc}", t0)
    _state.config = config
    _validate_config_coherence(config)

    # Step 2 — embedding model (failure -> degraded mode, §3.6)
    model = EmbeddingModel.instance()
    emb = config.get("embedding", {})
    try:
        if not getattr(model, "is_ready", False):
            model.load(
                emb.get("model_name"),
                cache_dir=emb.get("cache_dir"),
                model_version=emb.get("model_version"),
            )
        _state.model_ready = bool(getattr(model, "is_ready", False))
        if not _state.model_ready:
            raise RuntimeError("embedding model reported not ready after load")
    except Exception:  # noqa: BLE001
        logger.exception("Embedding model load failed; starting in degraded mode.")
        _state.startup_latency_ms = _elapsed_ms(t0)
        return _health_degraded(config, "model_not_ready")

    # Step 3 — old tickets pool (skip invalid / missing -> empty, never crash)
    try:
        records = _load_ticket_records(_old_tickets_path())
        _state.seed_ticket_pool, _state.seed_title_lookup = _embed_records(records, model, config)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to build seed ticket pool; continuing with empty pool.")
        _state.seed_ticket_pool, _state.seed_title_lookup = [], {}

    # Step 4 — knowledge base (cache build; Qdrant upsert deferred to step 5)
    kb = KnowledgeBase()
    try:
        articles = kb.load_articles(_articles_path())
        kb.build_article_embeddings(articles, model, config, qdrant=None)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to build article embeddings; KB will be empty.")
    _state.kb = kb

    # Step 5 — optional Qdrant
    _state.qdrant = _maybe_connect_qdrant(config, model, kb)

    # Step 6 — health
    _state.initialized = True
    _state.startup_latency_ms = _elapsed_ms(t0)
    return _health_ok(config)


# ---------------------------------------------------------------------------- #
# Per-request
# ---------------------------------------------------------------------------- #
def run_infrastructure(request: InfrastructureRequest) -> InfrastructureResult:
    """Analyze one ticket. Never raises; populates `error` on any failure (Rule 1)."""
    t0 = time.perf_counter()
    model = EmbeddingModel.instance()
    version = _safe_model_version(model)

    if not _state.initialized or not getattr(model, "is_ready", False):
        return _neutral_result(version, t0, "model_not_ready")

    config = _state.config

    # Defaults so partial results survive a later-stage failure (Rule 1 / per-stage).
    error: str | None = None
    similar: list = []
    related = None
    incident = IncidentCandidate(possible_incident=False)

    # Stages 1+2: standardized text + encode. Fatal — without a vector nothing else
    # can run, so we return a neutral result immediately.
    try:
        text = build_ticket_text(request.title, request.description, request.category)
        query_vector = model.encode(text)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Encoding failed; returning neutral result.")
        return _neutral_result(version, t0, f"encode_failed: {exc}")

    # Pool selection.
    #   * Qdrant available -> Qdrant is the seeded corpus; search it (titles via payload,
    #     seed_title_lookup as backup).
    #   * Qdrant not available (default) -> Python cosine over the pool the caller
    #     supplied in request.old_tickets. An empty pool yields empty results; we do
    #     NOT silently fall back to the seed pool (H6) — an empty live pool is valid.
    qa = _active_qdrant()
    if qa is not None:
        pool, titles, qdrant_for_search = _state.seed_ticket_pool, _state.seed_title_lookup, qa
    else:
        try:
            pool, titles = _embed_records(request.old_tickets, model, config)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Pool embedding failed; continuing with empty pool.")
            pool, titles = [], {}
            error = error or f"pool_embed_failed: {exc}"
        qdrant_for_search = None

    # Stage 3: similar tickets.
    try:
        similar = find_similar_tickets(
            query_vector,
            pool,
            config,
            query_ticket_id=request.ticket_id,
            title_lookup=titles,
            qdrant=qdrant_for_search,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Similarity search failed.")
        error = error or f"similarity_failed: {exc}"

    # Stage 4: related article (articles are seed-loaded; not per-request).
    try:
        if _state.kb is not None:
            related = _state.kb.find_related_article(query_vector, config, qdrant=qa)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Related-article lookup failed.")
        error = error or f"article_failed: {exc}"

    # Stage 5: incident candidate (consumes whatever similar tickets we have).
    try:
        incident = detect_incident_candidate(
            similar,
            request.category,
            config,
            open_incident_categories=getattr(request, "open_incident_categories", None),
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Incident detection failed.")
        incident = IncidentCandidate(possible_incident=False)
        error = error or f"incident_failed: {exc}"

    # Stage 6: assemble (guarded — even result construction must not raise to main.py).
    try:
        return InfrastructureResult(
            similar_tickets=similar,
            related_article=related,
            incident=incident,
            embedding_model_version=version,
            latency_ms=_elapsed_ms(t0),
            error=error,
        )
    except Exception:  # noqa: BLE001
        logger.exception("Result assembly failed; returning bare neutral result.")
        return _neutral_result(version, t0, error or "result_assembly_failed")


# ---------------------------------------------------------------------------- #
# Embedding the ticket pool (with cross-request cache, §9.3)
# ---------------------------------------------------------------------------- #
def _embed_records(
    records: list[OldTicketRecord], model: "EmbeddingModel", config: dict
) -> tuple[list[TicketVectorEntry], dict[int, str]]:
    pool: list[TicketVectorEntry] = []
    titles: dict[int, str] = {}

    pending_idx: list[int] = []
    pending_texts: list[str] = []
    pending_keys: list[tuple[int, str]] = []
    vectors: list[list[float] | None] = []

    for rec in records or []:
        text = build_ticket_text(rec.title, rec.description, rec.category)
        key = (rec.ticket_id, _text_hash(text))
        titles[rec.ticket_id] = rec.title
        cached = _state.ticket_vec_cache.get(key)
        if cached is not None:
            vectors.append(cached)
        else:
            vectors.append(None)
            pending_idx.append(len(vectors) - 1)
            pending_texts.append(text)
            pending_keys.append(key)

    if pending_texts:
        encoded = model.encode_batch(pending_texts)
        for slot, key, vec in zip(pending_idx, pending_keys, encoded):
            vectors[slot] = vec
            _state.ticket_vec_cache[key] = vec

    for rec, vec in zip(records or [], vectors):
        pool.append(
            TicketVectorEntry(
                ticket_id=rec.ticket_id,
                vector=vec or [],
                category=rec.category,
                status=rec.status,
            )
        )
    return pool, titles


# ---------------------------------------------------------------------------- #
# Qdrant wiring
# ---------------------------------------------------------------------------- #
def _maybe_connect_qdrant(
    config: dict, model: "EmbeddingModel", kb: KnowledgeBase
) -> QdrantAdapter | None:
    qcfg = config.get("qdrant", {})
    if not qcfg.get("enabled", False):
        logger.info("Qdrant disabled; using Python cosine fallback (Rule 8).")
        return QdrantAdapter.from_config(qcfg)  # available stays False

    adapter = QdrantAdapter.from_config(qcfg, api_key=os.environ.get("QDRANT_API_KEY"))
    if not adapter.health_check():
        return adapter  # not available -> fallback

    try:
        adapter.ensure_collections(int(model.dimension))
        # upsert seed tickets
        points = [
            {
                "id": e.ticket_id,
                "vector": e.vector,
                "payload": {
                    "ticket_id": e.ticket_id,
                    "category": e.category,
                    "status": e.status,
                    "title": _state.seed_title_lookup.get(e.ticket_id, ""),
                },
            }
            for e in _state.seed_ticket_pool
            if e.vector
        ]
        adapter.upsert(adapter.tickets_collection, points)
        # push articles to Qdrant (cache hit -> no recompute, just upsert)
        kb.build_article_embeddings(kb_articles_snapshot(kb), model, config, qdrant=adapter)
    except Exception:  # noqa: BLE001 - degrade to Python on any Qdrant error
        logger.exception("Qdrant index population failed; falling back to Python.")
        adapter.close()
    return adapter


def kb_articles_snapshot(kb: KnowledgeBase) -> list:
    """Re-load articles for the Qdrant upsert pass (cache makes embedding a no-op)."""
    return kb.load_articles(_articles_path())


def _active_qdrant() -> QdrantAdapter | None:
    q = _state.qdrant
    return q if (q is not None and getattr(q, "available", False)) else None


# ---------------------------------------------------------------------------- #
# Health builders
# ---------------------------------------------------------------------------- #
def _qdrant_mode(config: dict) -> str:
    enabled = config.get("qdrant", {}).get("enabled", False)
    if not enabled:
        return "disabled"
    return "active" if _active_qdrant() is not None else "fallback"


def _health_ok(config: dict) -> InfrastructureHealthStatus:
    model = EmbeddingModel.instance()
    return InfrastructureHealthStatus(
        status="ok",
        model_loaded=True,
        model_version=_safe_model_version(model),
        articles_indexed=(_state.kb.articles_indexed if _state.kb else 0),
        tickets_in_pool=len(_state.seed_ticket_pool),
        qdrant_available=_active_qdrant() is not None,
        qdrant_mode=_qdrant_mode(config),
        startup_latency_ms=_state.startup_latency_ms,
        error_reason=None,
    )


def _health_degraded(config: dict, reason: str) -> InfrastructureHealthStatus:
    return InfrastructureHealthStatus(
        status="degraded",
        model_loaded=False,
        model_version=config.get("embedding", {}).get("model_version", "unknown"),
        articles_indexed=0,
        tickets_in_pool=0,
        qdrant_available=False,
        qdrant_mode="disabled" if not config.get("qdrant", {}).get("enabled", False) else "fallback",
        startup_latency_ms=_state.startup_latency_ms,
        error_reason=reason,
    )


def _health_error(reason: str, t0: float) -> InfrastructureHealthStatus:
    return InfrastructureHealthStatus(
        status="error",
        model_loaded=False,
        model_version="unknown",
        articles_indexed=0,
        tickets_in_pool=0,
        qdrant_available=False,
        qdrant_mode="disabled",
        startup_latency_ms=_elapsed_ms(t0),
        error_reason=reason,
    )


# ---------------------------------------------------------------------------- #
# Result / misc helpers
# ---------------------------------------------------------------------------- #
def _neutral_result(version: str, t0: float, error: str) -> InfrastructureResult:
    return InfrastructureResult(
        similar_tickets=[],
        related_article=None,
        incident=IncidentCandidate(possible_incident=False),
        embedding_model_version=version,
        latency_ms=_elapsed_ms(t0),
        error=error,
    )


def _validate_config_coherence(config: dict) -> None:
    """Log WARNINGs for threshold incoherence. Never raises (coherence, not safety)."""
    sim = config.get("similarity", {})
    inc = config.get("incident_detection", {})
    try:
        floor = float(inc.get("similarity_floor"))
        t_sim = float(sim.get("threshold_similar"))
        if floor < t_sim:
            logger.warning(
                "Config coherence: incident_detection.similarity_floor (%.2f) < "
                "similarity.threshold_similar (%.2f); the floor has no effect because "
                "similar_tickets are already filtered at the higher threshold.", floor, t_sim
            )
    except (TypeError, ValueError):
        pass
    try:
        medium_max = int(inc.get("medium_max_tickets"))
        high_min = int(inc.get("high_min_tickets"))
        if medium_max + 1 != high_min:
            logger.warning(
                "Config coherence: medium_max_tickets (%d) + 1 != high_min_tickets (%d); "
                "severity bands are non-contiguous.", medium_max, high_min
            )
    except (TypeError, ValueError):
        pass


def _load_config() -> dict:
    path = os.environ.get("INFRASTRUCTURE_CONFIG_PATH", _DEFAULT_CONFIG_PATH)
    with open(path, "r", encoding="utf-8") as fh:
        config = json.load(fh)
    if not isinstance(config, dict):
        raise ValueError("infrastructure_config.json must be a JSON object")
    return config


def _load_ticket_records(path: str) -> list[OldTicketRecord]:
    if not os.path.exists(path):
        logger.warning("Old tickets file not found: %s; pool is empty.", path)
        return []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to read/parse %s; pool is empty.", path)
        return []
    out: list[OldTicketRecord] = []
    for rec in raw if isinstance(raw, list) else []:
        try:
            out.append(OldTicketRecord(**rec))
        except Exception as exc:  # noqa: BLE001 - skip invalid, never crash (Rule 7)
            logger.warning("Skipping invalid ticket record (%s): %r", exc, rec)
    logger.info("Loaded %d ticket records from %s.", len(out), path)
    return out


def _safe_model_version(model) -> str:
    return getattr(model, "model_version", None) or "unknown"


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _old_tickets_path() -> str:
    return os.environ.get("OLD_TICKETS_PATH", _DEFAULT_OLD_TICKETS_PATH)


def _articles_path() -> str:
    return os.environ.get("KNOWLEDGE_ARTICLES_PATH", _DEFAULT_ARTICLES_PATH)


def _elapsed_ms(t0: float) -> float:
    return round((time.perf_counter() - t0) * 1000.0, 2)