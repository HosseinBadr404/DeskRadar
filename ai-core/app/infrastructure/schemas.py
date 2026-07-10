"""
ServiceDesk Radar — AI Infrastructure
app/infrastructure/schemas.py  (Step 3)

Single location for ALL Pydantic models used by this module:
  - Input models      (received from main.py / loaded from seed data files)
  - Internal models   (in-memory or on-disk cache; never returned to the API)
  - Output models     (the `intelligence` block returned to main.py)
  - Evaluation models (offline reports produced by evaluation.py)

Architecture invariants enforced here:
  * Every data-file load is validated by a Pydantic model (Critical Rule 7).
  * Thresholds are NOT defined here — they live solely in
    config/infrastructure_config.json (Critical Rule 4).
  * This module imports nothing from analyzer/ (Critical Rule 5).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

# ==============================================================================
# Input Models
# ==============================================================================


class OldTicketRecord(BaseModel):
    """One ticket from the existing pool (data/old_tickets.json)."""

    ticket_id: int
    title: str
    description: str
    category: str
    status: str  # used for the deleted/closed filter in similarity_search


class KnowledgeArticle(BaseModel):
    """One knowledge-base article (data/knowledge_articles.json)."""

    article_id: int
    title: str
    content: str
    category: str
    tags: list[str] = Field(default_factory=list)


class OpenIncidentRecord(BaseModel):
    """Minimal open-incident context supplied by the Backend for deduplication."""

    incident_id: int = Field(gt=0)
    category: str = Field(min_length=1)
    matched_ticket_ids: set[int] = Field(default_factory=set)


class InfrastructureRequest(BaseModel):
    """Per-ticket request received by run_infrastructure()."""

    ticket_id: int = Field(gt=0)  # positive, required
    title: str = Field(min_length=1)  # non-empty, required
    description: str
    category: str | None = None  # optional — from Analyzer output
    old_tickets: list[OldTicketRecord] = Field(default_factory=list)
    open_incidents: list[OpenIncidentRecord] = Field(default_factory=list)


# ==============================================================================
# Internal Models  (never serialized to the API)
# ==============================================================================


class TicketVectorEntry(BaseModel):
    """In-memory ticket vector. Built at startup; never returned to main.py."""

    ticket_id: int
    vector: list[float]
    category: str
    status: str


class EmbeddingCacheEntry(BaseModel):
    """Persisted in data/.cache/article_embeddings.json."""

    article_id: int
    vector: list[float] = Field(min_length=1)
    model_version: str
    text_hash: str  # detects article content changes between startups


class TicketEmbeddingCacheEntry(BaseModel):
    """Persisted ticket embedding, reused across service restarts."""

    ticket_id: int
    vector: list[float] = Field(min_length=1)
    model_version: str
    text_hash: str  # changes whenever title, description, or category changes


# ==============================================================================
# Output Models
# ==============================================================================


class SimilarTicket(BaseModel):
    ticket_id: int
    similarity: float = Field(ge=0.0, le=1.0)  # 0.0 – 1.0
    match_level: Literal["similar", "very_similar"]
    title: str
    category: str


class RelatedArticle(BaseModel):
    article_id: int
    title: str
    score: float = Field(ge=0.0, le=1.0)
    category: str
    tags: list[str] = Field(default_factory=list)


class IncidentCandidate(BaseModel):
    possible_incident: bool
    severity: Literal["medium", "high"] | None = None
    fa_title_incident: str | None = None
    fa_reason_incident: str | None = None
    matched_ticket_ids: list[int] = Field(default_factory=list)
    avg_similarity_score: float | None = Field(default=None, ge=0.0, le=1.0)
    is_duplicate: bool = False
    duplicate_incident_id: int | None = None  # Backend updates this incident when present


class InfrastructureResult(BaseModel):
    similar_tickets: list[SimilarTicket] = Field(default_factory=list)
    related_article: RelatedArticle | None = None
    incident: IncidentCandidate
    embedding_model_version: str
    latency_ms: float
    error: str | None = None  # None = success; string = controlled failure


class InfrastructureHealthStatus(BaseModel):
    status: Literal["ok", "degraded", "error"]
    model_loaded: bool
    model_version: str
    articles_indexed: int
    tickets_in_pool: int
    qdrant_available: bool
    qdrant_mode: Literal["active", "fallback", "disabled"]
    startup_latency_ms: float
    error_reason: str | None = None


# ==============================================================================
# Evaluation Report Models  (offline only — evaluation.py)
# ==============================================================================


class SimilarityReport(BaseModel):
    total_pairs: int
    similar_pairs_avg_score: float
    dissimilar_pairs_avg_score: float
    separation_gap: float  # target > 0.15
    pass_rate: float
    recommended_threshold: float


class ThresholdReport(BaseModel):
    tested_thresholds: list[float] = Field(default_factory=list)
    pass_rates: list[float] = Field(default_factory=list)
    recommended_threshold: float


class CategoryReport(BaseModel):
    total_evaluated: int
    correct: int
    accuracy: float
    per_category: dict[str, float] = Field(default_factory=dict)


# ==============================================================================
# Configuration Models
# ==============================================================================


class EmbeddingConfig(BaseModel):
    model_name: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    cache_dir: str = Field(min_length=1)


class TicketEmbeddingConfig(BaseModel):
    cache_path: str = Field(min_length=1)


class SimilarityConfig(BaseModel):
    top_k: int = Field(ge=1)
    threshold_similar: float = Field(ge=0.0, le=1.0)
    threshold_very_similar: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def very_similar_must_not_be_lower(self):
        if self.threshold_very_similar < self.threshold_similar:
            raise ValueError("threshold_very_similar must be >= threshold_similar")
        return self


class KnowledgeBaseConfig(BaseModel):
    article_score_min: float = Field(ge=0.0, le=1.0)
    cache_path: str = Field(min_length=1)


class IncidentDetectionConfig(BaseModel):
    similarity_floor: float = Field(ge=0.0, le=1.0)
    medium_min_tickets: int = Field(ge=1)
    medium_max_tickets: int = Field(ge=1)
    high_min_tickets: int = Field(ge=1)

    @model_validator(mode="after")
    def medium_range_must_be_ordered(self):
        if self.medium_max_tickets < self.medium_min_tickets:
            raise ValueError("medium_max_tickets must be >= medium_min_tickets")
        return self


class QdrantConfig(BaseModel):
    enabled: bool
    host: str = Field(min_length=1)
    port: int = Field(ge=1, le=65535)
    collection_tickets: str = Field(min_length=1)
    collection_articles: str = Field(min_length=1)
    fallback_to_python: bool
    timeout_seconds: float = Field(gt=0.0)


class InfrastructureConfig(BaseModel):
    embedding: EmbeddingConfig
    ticket_embeddings: TicketEmbeddingConfig
    similarity: SimilarityConfig
    knowledge_base: KnowledgeBaseConfig
    incident_detection: IncidentDetectionConfig
    qdrant: QdrantConfig
