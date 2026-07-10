import logging
from pathlib import Path

from fastapi.testclient import TestClient

from app.infrastructure.embedding_model import set_model_for_testing
from app.main import _maybe_initialize_analyzer, app


class FailingEmbeddingModel:
    is_ready = False
    model_version = "failing-test-v1"
    dimension = 5

    def load(self, *args, **kwargs):
        raise RuntimeError("simulated model load failure")


def test_missing_analyzer_initializer_is_an_expected_infrastructure_only_mode(caplog):
    with caplog.at_level(logging.INFO):
        _maybe_initialize_analyzer()

    assert "Analyzer has no initializer; running Infrastructure only." in caplog.messages
    assert not [record for record in caplog.records if record.levelno >= logging.ERROR]


def test_health_returns_503_for_invalid_config(monkeypatch):
    monkeypatch.setenv("INFRASTRUCTURE_CONFIG_PATH", str(Path("missing-config.json").resolve()))

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["status"] == "error"
    assert response.json()["error_reason"].startswith("config_load_failed:")


def test_degraded_model_returns_controlled_neutral_analysis(monkeypatch):
    ai_core = Path(__file__).resolve().parent.parent
    monkeypatch.setenv(
        "INFRASTRUCTURE_CONFIG_PATH", str(ai_core / "config" / "infrastructure_config.json")
    )
    set_model_for_testing(FailingEmbeddingModel())

    with TestClient(app) as client:
        health = client.get("/health")
        analysis = client.post(
            "/analyze-ticket",
            json={
                "ticket_id": 1003,
                "title": "VPN unavailable",
                "description": "Cannot authenticate",
            },
        )

    assert health.status_code == 200
    assert health.json()["status"] == "degraded"
    assert health.json()["error_reason"] == "model_not_ready"
    assert analysis.status_code == 200
    assert analysis.json()["error"] == "model_not_ready"
    assert analysis.json()["similar_tickets"] == []
    assert analysis.json()["related_article"] is None
    assert analysis.json()["incident"]["possible_incident"] is False
