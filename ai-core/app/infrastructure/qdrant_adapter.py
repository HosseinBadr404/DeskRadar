"""
ServiceDesk Radar — AI Infrastructure
app/infrastructure/qdrant_adapter.py  (Step 13)

Optional Qdrant vector store, fully isolated behind this adapter.

Decision rule (handoff §3.2):
  * Qdrant is used ONLY when config.qdrant.enabled = true AND a startup health
    check succeeds. Otherwise `available` stays False and the caller silently
    uses the pure-Python cosine fallback (Critical Rule 8). The demo never
    depends on Qdrant.

Design notes:
  * The `qdrant_client` package is imported lazily inside methods, never at
    module import time. This keeps the module importable (and the Python
    fallback fully functional) even when qdrant-client is not installed.
  * This adapter is a thin transport: it stores/searches vectors and payloads.
    Domain filtering (self-match guard, deleted/closed filter) stays in
    similarity_search.py so the Qdrant and Python paths filter identically.
  * Two separate collections: `tickets` and `articles`.
  * Distance = Cosine, to match the Python cosine fallback so results do not
    differ sharply (Taskbook §9.7).
  * No thresholds are read or hardcoded here (Rule 4); vector size is supplied
    by the embedding model dimension; host/port/collection names come from config.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class QdrantAdapter:
    """Thin wrapper around qdrant-client. Construction never connects."""

    def __init__(
        self,
        *,
        enabled: bool,
        host: str,
        port: int,
        collection_tickets: str,
        collection_articles: str,
        api_key: str | None = None,
        timeout_seconds: float = 3.0,
    ) -> None:
        self._enabled = bool(enabled)
        self._host = host
        self._port = int(port)
        self._collection_tickets = collection_tickets
        self._collection_articles = collection_articles
        self._api_key = api_key or None
        self._timeout = float(timeout_seconds)

        self._client = None
        self._qdrant_available: bool = False

    # ------------------------------------------------------------------ #
    # Construction from config
    # ------------------------------------------------------------------ #
    @classmethod
    def from_config(cls, qdrant_config: dict, api_key: str | None = None) -> "QdrantAdapter":
        """Build from the `qdrant` block of infrastructure_config.json."""
        return cls(
            enabled=qdrant_config.get("enabled", False),
            host=qdrant_config.get("host", "localhost"),
            port=qdrant_config.get("port", 6333),
            collection_tickets=qdrant_config.get("collection_tickets", "tickets"),
            collection_articles=qdrant_config.get("collection_articles", "articles"),
            api_key=api_key,
            timeout_seconds=qdrant_config.get("timeout_seconds", 3.0),
        )

    # ------------------------------------------------------------------ #
    # Status / metadata
    # ------------------------------------------------------------------ #
    @property
    def available(self) -> bool:
        """True only after a successful health_check while enabled."""
        return self._qdrant_available

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def tickets_collection(self) -> str:
        return self._collection_tickets

    @property
    def articles_collection(self) -> str:
        return self._collection_articles

    # ------------------------------------------------------------------ #
    # Health
    # ------------------------------------------------------------------ #
    def health_check(self) -> bool:
        """
        Attempt to connect and ping Qdrant. Sets and returns `available`.

        Never raises: if disabled, qdrant-client is missing, or the server is
        unreachable, it logs and returns False so the caller falls back to
        Python cosine (Rule 8 / startup §5).
        """
        if not self._enabled:
            self._qdrant_available = False
            logger.info("Qdrant disabled in config; using Python cosine fallback.")
            return False

        try:
            client = self._ensure_client()
            # Lightweight round-trip to confirm the server responds.
            client.get_collections()
            self._qdrant_available = True
            logger.info("Qdrant health check OK at %s:%s.", self._host, self._port)
            return True
        except Exception as exc:  # noqa: BLE001 - degrade gracefully, never crash startup
            self._qdrant_available = False
            self._client = None
            logger.warning(
                "Qdrant health check failed (%s); falling back to Python cosine.", exc
            )
            return False

    # ------------------------------------------------------------------ #
    # Collections
    # ------------------------------------------------------------------ #
    def ensure_collections(self, vector_size: int) -> None:
        """
        Create the `tickets` and `articles` collections (Cosine distance) if they
        do not already exist. `vector_size` must match the embedding dimension.
        """
        self._require_available()
        from qdrant_client.http import models as qmodels

        client = self._ensure_client()
        existing = {c.name for c in client.get_collections().collections}
        for name in (self._collection_tickets, self._collection_articles):
            if name in existing:
                continue
            client.create_collection(
                collection_name=name,
                vectors_config=qmodels.VectorParams(
                    size=int(vector_size), distance=qmodels.Distance.COSINE
                ),
            )
            logger.info("Created Qdrant collection '%s' (size=%s, cosine).", name, vector_size)

    # ------------------------------------------------------------------ #
    # Upsert / Search
    # ------------------------------------------------------------------ #
    def upsert(self, collection: str, points: list[dict]) -> None:
        """
        Upsert points into a collection. Each point dict:
            {"id": int, "vector": list[float], "payload": dict}
        Payload should carry the domain id and the fields needed to rebuild a
        result (e.g. ticket_id, category, title, status / tags) so search results
        are self-contained.
        """
        self._require_available()
        if not points:
            return
        from qdrant_client.http import models as qmodels

        client = self._ensure_client()
        structs = [
            qmodels.PointStruct(
                id=p["id"], vector=p["vector"], payload=p.get("payload", {})
            )
            for p in points
        ]
        client.upsert(collection_name=collection, points=structs)
        logger.info("Upserted %d points into Qdrant collection '%s'.", len(structs), collection)

    def search(self, collection: str, vector: list[float], top_k: int) -> list[dict]:
        """
        Return up to `top_k` nearest points as
            [{"id": int, "score": float, "payload": dict}, ...]
        ordered by descending cosine score. Domain filtering (self-match,
        status) is applied by the caller for parity with the Python path.
        """
        self._require_available()
        client = self._ensure_client()
        hits = client.search(
            collection_name=collection,
            query_vector=vector,
            limit=int(top_k),
            with_payload=True,
        )
        return [
            {"id": h.id, "score": float(h.score), "payload": dict(h.payload or {})}
            for h in hits
        ]

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def close(self) -> None:
        if self._client is not None:
            try:
                self._client.close()
            except Exception:  # noqa: BLE001
                pass
            finally:
                self._client = None
                self._qdrant_available = False

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _ensure_client(self):
        """Lazily construct the QdrantClient (deferred import keeps Rule 8 intact)."""
        if self._client is None:
            from qdrant_client import QdrantClient

            self._client = QdrantClient(
                host=self._host,
                port=self._port,
                api_key=self._api_key,
                timeout=self._timeout,
            )
        return self._client

    def _require_available(self) -> None:
        if not self._qdrant_available:
            raise RuntimeError(
                "Qdrant is not available. Callers must check `.available` and use "
                "the Python cosine fallback when it is False."
            )