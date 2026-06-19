"""
ServiceDesk Radar — AI Infrastructure
app/infrastructure/knowledge_base.py  (Step 15)

Knowledge-base retrieval. Provides:
  * load_articles(path)            — read + validate knowledge_articles.json.
  * build_article_embeddings(...)  — embed each article once, with a persistent
                                     cache keyed by model_version + text_hash.
  * find_related_article(vec, cfg) — nearest article, or None below the floor.

Cache behaviour (handoff §3.5 / startup §4 / Milestone 3):
  * Cache file: data/.cache/article_embeddings.json (path from config).
  * On build: for each article, if a cache entry exists whose model_version
    matches config AND whose text_hash matches the current article text, the
    cached vector is reused (no re-encode). Otherwise it is recomputed and the
    cache is overwritten. A second startup with unchanged articles/model does
    NOT recompute anything.

Retrieval:
  * Pure-Python cosine over the in-memory article index is the default.
  * If an available QdrantAdapter is supplied, the `articles` collection is used
    instead (Rule 8 keeps Python as the always-available fallback).

Invariants: no analyzer/ import (Rule 5); article_score_min comes from config
(Rule 4 — no numeric threshold hardcoded here).
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .schemas import EmbeddingCacheEntry, KnowledgeArticle, RelatedArticle

if TYPE_CHECKING:  # type-only imports; no runtime coupling
    from .embedding_model import EmbeddingModel
    from .qdrant_adapter import QdrantAdapter

logger = logging.getLogger(__name__)

_DEFAULT_CACHE_PATH = "data/.cache/article_embeddings.json"


class KnowledgeBase:
    """Holds the in-memory article index and serves related-article lookups."""

    def __init__(self) -> None:
        # article_id -> (vector, KnowledgeArticle)
        self._index: dict[int, tuple[list[float], KnowledgeArticle]] = {}

    # ------------------------------------------------------------------ #
    # Status
    # ------------------------------------------------------------------ #
    @property
    def articles_indexed(self) -> int:
        return len(self._index)

    # ------------------------------------------------------------------ #
    # Loading + validation (Rule 7)
    # ------------------------------------------------------------------ #
    def load_articles(self, path: str) -> list[KnowledgeArticle]:
        """Load and validate articles; invalid records are skipped with a WARNING."""
        p = Path(path)
        if not p.exists():
            logger.warning("Knowledge articles file not found: %s; no articles loaded.", path)
            return []
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            logger.exception("Failed to read/parse %s; no articles loaded.", path)
            return []
        if not isinstance(raw, list):
            logger.warning("Knowledge articles file %s is not a list; no articles loaded.", path)
            return []

        articles: list[KnowledgeArticle] = []
        for rec in raw:
            try:
                articles.append(KnowledgeArticle(**rec))
            except Exception as exc:  # noqa: BLE001 - skip invalid, never crash
                logger.warning("Skipping invalid knowledge article (%s): %r", exc, rec)
        logger.info("Loaded %d knowledge articles from %s.", len(articles), path)
        return articles

    # ------------------------------------------------------------------ #
    # Embedding + cache
    # ------------------------------------------------------------------ #
    def build_article_embeddings(
        self,
        articles: list[KnowledgeArticle],
        model: "EmbeddingModel",
        config: dict,
        *,
        qdrant: "QdrantAdapter | None" = None,
    ) -> int:
        """
        Build (or load from cache) one embedding per article and populate the
        in-memory index. Returns the number of indexed articles.
        """
        model_version = self._expected_model_version(config, model)
        cache_path = config.get("knowledge_base", {}).get("cache_path", _DEFAULT_CACHE_PATH)
        cache = self._load_cache(cache_path)

        index: dict[int, tuple[list[float], KnowledgeArticle]] = {}
        pending_texts: list[str] = []
        pending: list[tuple[KnowledgeArticle, str]] = []  # (article, text_hash)
        recompute = False

        # Expected embedding dimension, used to reject corrupt/stale cache vectors
        # (e.g. an empty [] written by a failed encode). None if unavailable.
        try:
            expected_dim = int(model.dimension)
        except Exception:  # noqa: BLE001
            expected_dim = None

        for art in articles:
            text = self._article_text(art)
            text_hash = self._text_hash(text)
            entry = cache.get(art.article_id)
            cache_valid = (
                entry is not None
                and entry.model_version == model_version
                and entry.text_hash == text_hash
                and len(entry.vector) > 0
                and (expected_dim is None or len(entry.vector) == expected_dim)
            )
            if cache_valid:
                index[art.article_id] = (entry.vector, art)  # reuse cached vector
            else:
                if entry is not None and not cache_valid:
                    logger.warning(
                        "Cache entry for article %s invalid (dim/model/text mismatch); recomputing.",
                        art.article_id,
                    )
                pending.append((art, text_hash))
                pending_texts.append(text)
                recompute = True

        if pending_texts:
            logger.info("Embedding %d article(s) (cache miss / changed).", len(pending_texts))
            vectors = model.encode_batch(pending_texts)
            for (art, text_hash), vector in zip(pending, vectors):
                index[art.article_id] = (vector, art)
                cache[art.article_id] = EmbeddingCacheEntry(
                    article_id=art.article_id,
                    vector=vector,
                    model_version=model_version,
                    text_hash=text_hash,
                )
        else:
            logger.info("All %d article embeddings served from cache (no recompute).", len(index))

        # Keep cache limited to currently-present articles.
        pruned = {aid: cache[aid] for aid in index if aid in cache}
        if recompute or len(pruned) != len(cache):
            self._write_cache(cache_path, pruned)

        self._index = index

        if qdrant is not None and getattr(qdrant, "available", False):
            self._upsert_qdrant(index, qdrant)

        return self.articles_indexed

    # ------------------------------------------------------------------ #
    # Retrieval
    # ------------------------------------------------------------------ #
    def find_related_article(
        self,
        query_vector: list[float],
        config: dict,
        *,
        qdrant: "QdrantAdapter | None" = None,
    ) -> RelatedArticle | None:
        """Return the single most relevant article, or None if below the floor."""
        score_min = float(config.get("knowledge_base", {}).get("article_score_min", 0.0))
        if not query_vector:
            return None

        if qdrant is not None and getattr(qdrant, "available", False):
            return self._find_qdrant(query_vector, score_min, qdrant)
        return self._find_python(query_vector, score_min)

    def _find_python(self, query_vector: list[float], score_min: float) -> RelatedArticle | None:
        best_score = -1.0
        best_article: KnowledgeArticle | None = None
        for vector, art in self._index.values():
            score = _cosine(query_vector, vector)
            if score > best_score:
                best_score, best_article = score, art
        if best_article is None or best_score < score_min:
            return None
        return RelatedArticle(
            article_id=best_article.article_id,
            title=best_article.title,
            score=round(_clamp01(best_score), 4),
            category=best_article.category,
            tags=list(best_article.tags),
        )

    def _find_qdrant(
        self, query_vector: list[float], score_min: float, qdrant: "QdrantAdapter"
    ) -> RelatedArticle | None:
        try:
            hits = qdrant.search(qdrant.articles_collection, query_vector, 1)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Qdrant article search failed (%s); returning None.", exc)
            return None
        if not hits:
            return None
        h = hits[0]
        score = _clamp01(float(h.get("score", 0.0)))
        if score < score_min:
            return None
        payload = h.get("payload", {}) or {}
        return RelatedArticle(
            article_id=int(payload.get("article_id", h.get("id"))),
            title=payload.get("title", ""),
            score=round(score, 4),
            category=payload.get("category", ""),
            tags=list(payload.get("tags", []) or []),
        )

    # ------------------------------------------------------------------ #
    # Cache I/O
    # ------------------------------------------------------------------ #
    def _load_cache(self, cache_path: str) -> dict[int, EmbeddingCacheEntry]:
        p = Path(cache_path)
        if not p.exists():
            return {}
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            logger.warning("Could not read article cache %s; will recompute.", cache_path)
            return {}
        out: dict[int, EmbeddingCacheEntry] = {}
        for rec in raw if isinstance(raw, list) else []:
            try:
                entry = EmbeddingCacheEntry(**rec)
                out[entry.article_id] = entry
            except Exception as exc:  # noqa: BLE001
                logger.warning("Skipping invalid cache entry (%s): %r", exc, rec)
        return out

    def _write_cache(self, cache_path: str, cache: dict[int, EmbeddingCacheEntry]) -> None:
        p = Path(cache_path)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            payload = [
                {
                    "article_id": e.article_id,
                    "vector": e.vector,
                    "model_version": e.model_version,
                    "text_hash": e.text_hash,
                }
                for e in cache.values()
            ]
            p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            logger.info("Wrote %d article embeddings to cache %s.", len(payload), cache_path)
        except Exception:  # noqa: BLE001 - cache is an optimization; never crash startup
            logger.exception("Failed to write article cache %s.", cache_path)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _upsert_qdrant(
        self, index: dict[int, tuple[list[float], KnowledgeArticle]], qdrant: "QdrantAdapter"
    ) -> None:
        try:
            points = [
                {
                    "id": aid,
                    "vector": vector,
                    "payload": {
                        "article_id": aid,
                        "title": art.title,
                        "category": art.category,
                        "tags": list(art.tags),
                    },
                }
                for aid, (vector, art) in index.items()
            ]
            qdrant.upsert(qdrant.articles_collection, points)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Qdrant article upsert failed (%s); Python retrieval still works.", exc)

    @staticmethod
    def _expected_model_version(config: dict, model: "EmbeddingModel") -> str:
        configured = config.get("embedding", {}).get("model_version")
        return configured or getattr(model, "model_version", None) or "unknown"

    @staticmethod
    def _article_text(article: KnowledgeArticle) -> str:
        parts = [article.title or "", article.content or ""]
        parts.extend(article.tags or [])
        return " ".join(s.strip() for s in parts if s and s.strip()).strip()

    @staticmethod
    def _text_hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------- #
# Cosine (local copy keeps knowledge_base independent of similarity_search)
# ---------------------------------------------------------------------------- #
def _cosine(a: list[float], b: list[float]) -> float:
    # INTENTIONALLY duplicated in similarity_search.py to avoid a cross-import
    # between sibling modules. Keep identical: dot/(norm*norm) clamped to [0,1].
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