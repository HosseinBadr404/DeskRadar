"""
ServiceDesk Radar — AI Infrastructure
app/infrastructure/similarity_search.py  (Step 14)

find_similar_tickets(): given the query ticket's embedding and the existing
ticket pool, return the top-k semantically similar tickets as list[SimilarTicket].

Behaviour (handoff §9.4 / Milestone 2):
  * Pure-Python cosine over the in-memory pool is the always-available default.
  * If an *available* QdrantAdapter is supplied, search runs against Qdrant
    instead; domain filtering is applied identically to both paths so results
    stay in parity (Rule 8 / Taskbook §9.7).
  * Self-match guard: the query ticket_id never appears in the results.
  * Deleted/closed tickets are filtered out.
  * top_k and the similar / very_similar thresholds come from config
    (Rule 4 — no numeric threshold hardcoded here).
  * Only tickets that reach the "similar" floor are returned (SimilarTicket
    has no match level below "similar"), sorted by descending similarity.

This module imports nothing from analyzer/ (Rule 5).
"""

from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING, Any

from .schemas import SimilarTicket, TicketVectorEntry

if TYPE_CHECKING:  # type-only import; no runtime coupling / no heavy deps
    from .qdrant_adapter import QdrantAdapter

logger = logging.getLogger(__name__)

# Statuses that disqualify a ticket from similarity results (Taskbook §9.4:
# "filter deleted/closed"). This is a categorical policy, not a numeric
# threshold, so it is a named constant rather than a config value.
EXCLUDED_STATUSES: frozenset[str] = frozenset({"closed", "deleted"})


def find_similar_tickets(
    query_vector: list[float],
    ticket_pool: list[TicketVectorEntry],
    config: dict,
    *,
    query_ticket_id: int | None = None,
    title_lookup: dict[int, str] | None = None,
    qdrant: "QdrantAdapter | None" = None,
) -> list[SimilarTicket]:
    """
    Parameters
    ----------
    query_vector : embedding of the incoming ticket (from EmbeddingModel.encode).
    ticket_pool  : in-memory list[TicketVectorEntry] built at startup.
    config       : full infrastructure config (or its "similarity" sub-block).
    query_ticket_id : id of the incoming ticket, excluded from results (self-match guard).
    title_lookup : {ticket_id: title}; supplies SimilarTicket.title for the Python
                   path, since TicketVectorEntry intentionally carries no title.
                   (The Qdrant path reads title from the point payload instead.)
    qdrant       : an optional QdrantAdapter; used only when it reports `.available`.

    Returns
    -------
    list[SimilarTicket] sorted by descending similarity, length <= top_k.
    """
    top_k, threshold_similar, threshold_very = _read_similarity_config(config)

    if not query_vector:
        return []

    use_qdrant = qdrant is not None and getattr(qdrant, "available", False)
    if use_qdrant:
        candidates = _candidates_from_qdrant(query_vector, qdrant, top_k)
    else:
        candidates = _candidates_from_pool(query_vector, ticket_pool, title_lookup)

    return _rank_and_label(
        candidates,
        query_ticket_id=query_ticket_id,
        top_k=top_k,
        threshold_similar=threshold_similar,
        threshold_very=threshold_very,
    )


# ---------------------------------------------------------------------------- #
# Candidate builders (each yields dicts: ticket_id, similarity, category, status, title)
# ---------------------------------------------------------------------------- #
def _candidates_from_pool(
    query_vector: list[float],
    ticket_pool: list[TicketVectorEntry],
    title_lookup: dict[int, str] | None,
) -> list[dict[str, Any]]:
    titles = title_lookup or {}
    out: list[dict[str, Any]] = []
    for entry in ticket_pool or []:
        sim = _cosine(query_vector, entry.vector)
        out.append(
            {
                "ticket_id": entry.ticket_id,
                "similarity": sim,
                "category": entry.category,
                "status": entry.status,
                "title": titles.get(entry.ticket_id, ""),
            }
        )
    return out


def _candidates_from_qdrant(
    query_vector: list[float],
    qdrant: "QdrantAdapter",
    top_k: int,
) -> list[dict[str, Any]]:
    # Over-fetch so the self-match / status filtering below still leaves >= top_k.
    limit = top_k * 2 + 10
    try:
        hits = qdrant.search(qdrant.tickets_collection, query_vector, limit)
    except Exception as exc:  # noqa: BLE001 - degrade to empty; caller path stays safe
        logger.warning("Qdrant search failed (%s); returning no Qdrant candidates.", exc)
        return []

    out: list[dict[str, Any]] = []
    for h in hits:
        payload = h.get("payload", {}) or {}
        ticket_id = payload.get("ticket_id", h.get("id"))
        out.append(
            {
                "ticket_id": ticket_id,
                "similarity": _clamp01(float(h.get("score", 0.0))),
                "category": payload.get("category", ""),
                "status": payload.get("status", ""),
                "title": payload.get("title", ""),
            }
        )
    return out


# ---------------------------------------------------------------------------- #
# Ranking / filtering (shared by both paths for parity)
# ---------------------------------------------------------------------------- #
def _rank_and_label(
    candidates: list[dict[str, Any]],
    *,
    query_ticket_id: int | None,
    top_k: int,
    threshold_similar: float,
    threshold_very: float,
) -> list[SimilarTicket]:
    results: list[SimilarTicket] = []
    for c in candidates:
        tid = c.get("ticket_id")

        # Self-match guard.
        if query_ticket_id is not None and tid == query_ticket_id:
            continue

        # Deleted/closed filter.
        if str(c.get("status") or "").lower() in EXCLUDED_STATUSES:
            continue

        sim = float(c.get("similarity", 0.0))
        if sim < threshold_similar:  # below the "similar" floor -> not returned
            continue

        level = "very_similar" if sim >= threshold_very else "similar"
        results.append(
            SimilarTicket(
                ticket_id=int(tid),
                similarity=round(_clamp01(sim), 4),
                match_level=level,
                title=c.get("title") or "",
                category=c.get("category") or "",
            )
        )

    results.sort(key=lambda s: s.similarity, reverse=True)
    return results[:top_k]


# ---------------------------------------------------------------------------- #
# Helpers
# ---------------------------------------------------------------------------- #
def _read_similarity_config(config: dict) -> tuple[int, float, float]:
    sim = config.get("similarity", config)
    return (
        int(sim["top_k"]),
        float(sim["threshold_similar"]),
        float(sim["threshold_very_similar"]),
    )


def _cosine(a: list[float], b: list[float]) -> float:
    """Pure-Python cosine similarity, clamped to [0, 1] to satisfy the schema.

    INTENTIONALLY duplicated in knowledge_base.py to avoid a cross-import
    between sibling modules. Keep the formula identical in both copies:
    dot(a, b) / (norm(a) * norm(b)), clamped to [0.0, 1.0].
    """
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = na = nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0.0 or nb == 0.0:
        return 0.0
    return _clamp01(dot / (math.sqrt(na) * math.sqrt(nb)))


def _clamp01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value