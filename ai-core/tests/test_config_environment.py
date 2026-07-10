import json
from pathlib import Path

from app.infrastructure import initialize_infrastructure
from app.infrastructure import _qdrant_config_with_environment


def test_invalid_threshold_config_fails_startup_cleanly(tmp_path, monkeypatch):
    ai_core = Path(__file__).resolve().parent.parent
    config = json.loads(
        (ai_core / "config" / "infrastructure_config.json").read_text(encoding="utf-8")
    )
    config["similarity"]["threshold_similar"] = 0.90
    config["similarity"]["threshold_very_similar"] = 0.80
    config_path = tmp_path / "invalid-config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    monkeypatch.setenv("INFRASTRUCTURE_CONFIG_PATH", str(config_path))

    health = initialize_infrastructure()

    assert health.status == "error"
    assert health.error_reason.startswith("config_load_failed:")


def test_hf_home_environment_overrides_embedding_cache_dir(
    tmp_path, monkeypatch, inject_mock_model
):
    ai_core = Path(__file__).resolve().parent.parent
    fixtures = Path(__file__).resolve().parent / "fixtures"
    config = json.loads(
        (ai_core / "config" / "infrastructure_config.json").read_text(encoding="utf-8")
    )
    config["ticket_embeddings"]["cache_path"] = str(tmp_path / "ticket_embeddings.json")
    config["knowledge_base"]["cache_path"] = str(tmp_path / "article_embeddings.json")
    config_path = tmp_path / "infrastructure_config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    requested_cache_dirs: list[str | None] = []

    def recording_load(model_name, cache_dir=None, model_version=None):
        requested_cache_dirs.append(cache_dir)
        inject_mock_model.model_version = model_version or "mock-v1"
        inject_mock_model.is_ready = True

    inject_mock_model.is_ready = False
    inject_mock_model.load = recording_load
    monkeypatch.setenv("HF_HOME", str(tmp_path / "model-cache"))
    monkeypatch.setenv("INFRASTRUCTURE_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("OLD_TICKETS_PATH", str(fixtures / "tickets_small.json"))
    monkeypatch.setenv("KNOWLEDGE_ARTICLES_PATH", str(fixtures / "articles_small.json"))

    health = initialize_infrastructure()

    assert health.status == "ok"
    assert requested_cache_dirs == [str(tmp_path / "model-cache")]


def test_qdrant_environment_overrides_are_validated(monkeypatch):
    config = {"host": "config-host", "port": 6333}

    monkeypatch.setenv("QDRANT_HOST", "env-host")
    monkeypatch.setenv("QDRANT_PORT", "7444")
    overridden = _qdrant_config_with_environment(config)
    assert overridden == {"host": "env-host", "port": 7444}
    assert config == {"host": "config-host", "port": 6333}

    monkeypatch.setenv("QDRANT_PORT", "not-a-port")
    invalid_port = _qdrant_config_with_environment(config)
    assert invalid_port == {"host": "env-host", "port": 6333}
