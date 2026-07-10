"""
ServiceDesk Radar — AI Core
app/main.py  

FastAPI entrypoint. This file wires the HTTP surface to the Infrastructure
module and (optionally, if present) the Analyzer module.

Boundaries (handoff §3.3 / reviewer B6):
  * `app/infrastructure/` is never coupled to the Analyzer. This entrypoint may
    initialize the Analyzer, but it does so behind a guarded, optional import so
    that the Infrastructure service starts and serves even when the Analyzer is
    absent or fails. Infrastructure never depends on the Analyzer's result.
  * Infrastructure exposes exactly two routes here:
        GET  /health         -> InfrastructureHealthStatus
        POST /analyze-ticket -> InfrastructureResult (the `intelligence` block)
    A combined Analyzer+Infrastructure endpoint, if ever needed, is orchestrated
    at this entrypoint level under a different route — never inside infrastructure/.

Contracts:
  * `initialize_infrastructure()` runs once in the lifespan; it never raises.
  * `run_infrastructure()` never raises; partial failures surface in the
    `error` field, so /analyze-ticket returns HTTP 200 with that field set.
  * /health returns 200 when the service is usable (ok / degraded) and 503 when
    it is not (error), so monitors don't treat an unusable service as healthy.
"""

from __future__ import annotations

import importlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response

from app.infrastructure import initialize_infrastructure, run_infrastructure
from app.infrastructure.schemas import (
    InfrastructureHealthStatus,
    InfrastructureRequest,
    InfrastructureResult,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup once: initialize Infrastructure, then optionally the Analyzer."""
    app.state.infra_health = initialize_infrastructure()
    logger.info(
        "Infrastructure initialized: status=%s model_loaded=%s articles=%s tickets=%s qdrant=%s",
        app.state.infra_health.status,
        app.state.infra_health.model_loaded,
        app.state.infra_health.articles_indexed,
        app.state.infra_health.tickets_in_pool,
        app.state.infra_health.qdrant_mode,
    )
    _maybe_initialize_analyzer()
    yield
    # No teardown required for the infrastructure layer.


app = FastAPI(
    title="ServiceDesk Radar — AI Core (Infrastructure)",
    version="1.0.0",
    description=(
        "Embedding-based similarity search, knowledge retrieval, and incident "
        "detection for ServiceDesk Radar tickets."
    ),
    lifespan=lifespan,
)


@app.get(
    "/health",
    response_model=InfrastructureHealthStatus,
    summary="Infrastructure readiness",
)
def health(request: Request, response: Response) -> InfrastructureHealthStatus:
    """
    Report Infrastructure readiness. HTTP 200 when usable (ok/degraded),
    503 when not (error). The Backend should check this before analysis.
    """
    status: InfrastructureHealthStatus = request.app.state.infra_health
    response.status_code = 200 if status.status in ("ok", "degraded") else 503
    return status


@app.post(
    "/analyze-ticket",
    response_model=InfrastructureResult,
    summary="Analyze a ticket (infrastructure intelligence block)",
)
def analyze_ticket(payload: InfrastructureRequest) -> InfrastructureResult:
    """
    Return similar tickets, the most relevant article, and an incident
    candidate for the given ticket. Always HTTP 200; controlled failures are
    reported in the result's `error` field (the Backend then sets
    analysis_status = "partial"/"failed").
    """
    return run_infrastructure(payload)


# ---------------------------------------------------------------------------- #
# Optional, guarded Analyzer initialization (keeps Rule 5 intact)
# ---------------------------------------------------------------------------- #
def _maybe_initialize_analyzer() -> None:
    """
    Initialize the Analyzer only if its module is installed. Its presence,
    absence, or failure must never affect the Infrastructure service.
    """
    try:
        analyzer = importlib.import_module("app.analyzer")
    except ModuleNotFoundError:
        logger.info("Analyzer module not present; running Infrastructure only.")
        return

    initialize_analyzer = getattr(analyzer, "initialize_analyzer", None)
    if not callable(initialize_analyzer):
        logger.info("Analyzer has no initializer; running Infrastructure only.")
        return

    try:
        initialize_analyzer()
        logger.info("Analyzer initialized.")
    except Exception:  # noqa: BLE001 - Analyzer failure must not break Infrastructure
        logger.exception("Analyzer initialization failed; Infrastructure unaffected.")
