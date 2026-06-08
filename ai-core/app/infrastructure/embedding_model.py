"""
ServiceDesk Radar — AI Infrastructure
app/infrastructure/embedding_model.py  (Step 12)

The embedding layer. Provides:
  * EmbeddingModel        — a process-wide singleton wrapping the
                            sentence-transformers model. Loaded EXACTLY ONCE at
                            startup via EmbeddingModel.instance().load(...).
  * build_ticket_text()   — turns (title, description, category?) into a single
                            standardized string, identical for every ticket.
  * encode()              — text -> list[float] vector.
  * ModelNotReadyError    — raised when encode() is called before load().
  * set_model_for_testing — injects a mock singleton (guarded: ENVIRONMENT=test).

Architecture invariants enforced here:
  * Rule 3: the model is NEVER loaded at import time. The heavy
    `sentence_transformers` import happens inside load(), not at module top.
  * Rule 4: no thresholds are read or hardcoded here; model_name / cache_dir /
    model_version are passed in by initialize_infrastructure() from config.
  * Rule 5: this module imports nothing from analyzer/.
"""

from __future__ import annotations

import logging
import os
import threading

logger = logging.getLogger(__name__)


class ModelNotReadyError(RuntimeError):
    """Raised when the embedding model is used before it has been loaded."""


def build_ticket_text(
    title: str | None,
    description: str | None,
    category: str | None = None,
) -> str:
    """
    Build the standardized text representation of a ticket for embedding.

    The same format is applied to every ticket (pool tickets at startup and the
    incoming query ticket) so vectors are comparable. `category` is optional
    (it may come from the Analyzer) and is prepended as a light hint when present.

    Examples
    --------
    >>> build_ticket_text("VPN وصل نمیشه", "خطای احراز هویت میده", "vpn")
    '[vpn] VPN وصل نمیشه خطای احراز هویت میده'
    >>> build_ticket_text("VPN وصل نمیشه", "خطای احراز هویت میده")
    'VPN وصل نمیشه خطای احراز هویت میده'
    """
    title = (title or "").strip()
    description = (description or "").strip()
    category = (category or "").strip()

    parts: list[str] = []
    if category:
        parts.append(f"[{category}]")
    if title:
        parts.append(title)
    if description:
        parts.append(description)

    return " ".join(parts).strip()


class EmbeddingModel:
    """
    Singleton wrapper around the sentence-transformers embedding model.

    Lifecycle:
        EmbeddingModel.instance()            # get the singleton (no model loaded)
        EmbeddingModel.instance().load(...)  # load weights ONCE at startup
        EmbeddingModel.instance().encode(t)  # per ticket / per article

    The model is loaded only inside load() and is idempotent: repeated load()
    calls for the same model_name do not reload the weights (Milestone 1: "100
    encode() calls load the model exactly once").
    """

    _instance: "EmbeddingModel | None" = None
    _instance_lock = threading.Lock()

    def __init__(self) -> None:
        self._model = None  # the underlying SentenceTransformer (or a mock)
        self._model_name: str | None = None
        self._model_version: str | None = None
        self._cache_dir: str | None = None
        self._model_ready: bool = False
        self._load_lock = threading.Lock()

    # ------------------------------------------------------------------ #
    # Singleton access
    # ------------------------------------------------------------------ #
    @classmethod
    def instance(cls) -> "EmbeddingModel":
        """Return the process-wide singleton, creating it if necessary.

        Creating the instance does NOT load any model (Rule 3)."""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------ #
    # Loading
    # ------------------------------------------------------------------ #
    def load(
        self,
        model_name: str,
        cache_dir: str | None = None,
        model_version: str | None = None,
    ) -> None:
        """
        Load the embedding model weights. Called once by
        initialize_infrastructure() (startup Step 2).

        Idempotent: if the same model_name is already loaded, this is a no-op.
        Raises on failure so the caller can record status="error" / degraded mode;
        it never silently leaves the instance half-initialized.
        """
        with self._load_lock:
            if self._model is not None and self._model_name == model_name:
                logger.info("Embedding model '%s' already loaded; skipping reload.", model_name)
                self._model_version = model_version or self._model_version
                self._model_ready = True
                return

            logger.info("Loading embedding model '%s' (cache_dir=%s) ...", model_name, cache_dir)
            # Heavy import is deferred to load-time so importing this module never
            # pulls in or initializes the model (Rule 3) and so tests that inject
            # a mock do not require sentence-transformers to be installed.
            from sentence_transformers import SentenceTransformer

            try:
                self._model = SentenceTransformer(model_name, cache_folder=cache_dir)
            except Exception:
                self._model = None
                self._model_ready = False
                logger.exception("Failed to load embedding model '%s'.", model_name)
                raise

            self._model_name = model_name
            self._model_version = model_version or model_name
            self._cache_dir = cache_dir
            self._model_ready = True
            logger.info("Embedding model '%s' loaded (version=%s).", model_name, self._model_version)

    # ------------------------------------------------------------------ #
    # Status / metadata
    # ------------------------------------------------------------------ #
    @property
    def is_ready(self) -> bool:
        return self._model_ready and self._model is not None

    @property
    def model_name(self) -> str | None:
        return self._model_name

    @property
    def model_version(self) -> str | None:
        """Provenance string surfaced as InfrastructureResult.embedding_model_version."""
        return self._model_version

    @property
    def dimension(self) -> int:
        """Embedding vector size (used to create the Qdrant collection)."""
        self._ensure_ready()
        get_dim = getattr(self._model, "get_sentence_embedding_dimension", None)
        if callable(get_dim):
            return int(get_dim())
        # Fallback: derive from a probe encode (covers mocks without the method).
        return len(self.encode("dimension_probe"))

    # ------------------------------------------------------------------ #
    # Encoding
    # ------------------------------------------------------------------ #
    def encode(self, text: str) -> list[float]:
        """Encode a single text into a JSON-serializable list[float] vector."""
        self._ensure_ready()
        vector = self._model.encode((text or "").strip())
        return self._to_float_list(vector)

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Encode many texts in one call (used at startup to embed the ticket pool
        and the knowledge-base articles efficiently). Order is preserved.
        """
        self._ensure_ready()
        cleaned = [(t or "").strip() for t in texts]
        if not cleaned:
            return []
        vectors = self._model.encode(cleaned)
        return [self._to_float_list(v) for v in vectors]

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _ensure_ready(self) -> None:
        if not self.is_ready:
            raise ModelNotReadyError(
                "Embedding model is not loaded. "
                "Call EmbeddingModel.instance().load(...) in initialize_infrastructure()."
            )

    @staticmethod
    def _to_float_list(vector) -> list[float]:
        """Coerce a numpy array / list / scalar-bearing iterable to list[float]."""
        tolist = getattr(vector, "tolist", None)
        if callable(tolist):
            vector = tolist()
        return [float(x) for x in vector]


# ---------------------------------------------------------------------------- #
# Test-only injection
# ---------------------------------------------------------------------------- #
def _is_test_environment() -> bool:
    return os.environ.get("ENVIRONMENT", "").strip().lower() == "test"


def set_model_for_testing(mock) -> None:
    """
    Replace the EmbeddingModel singleton with a mock object.

    Guard: only permitted when ENVIRONMENT=test, so it can never silently
    substitute the model in development or production.

    The mock is expected to expose the same surface used downstream
    (`encode`, `encode_batch`, `is_ready`, `model_version`, `dimension`).
    """
    if not _is_test_environment():
        raise RuntimeError(
            "set_model_for_testing() is only allowed when ENVIRONMENT=test."
        )
    EmbeddingModel._instance = mock
    logger.warning("EmbeddingModel singleton replaced with a test mock.")


def reset_model_for_testing() -> None:
    """Drop the singleton so the next instance() call rebuilds it. ENVIRONMENT=test only."""
    if not _is_test_environment():
        raise RuntimeError(
            "reset_model_for_testing() is only allowed when ENVIRONMENT=test."
        )
    EmbeddingModel._instance = None
    logger.warning("EmbeddingModel singleton reset for testing.")