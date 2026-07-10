import json
from pathlib import Path

from app.infrastructure import initialize_infrastructure, run_infrastructure
from app.infrastructure.schemas import InfrastructureRequest, OldTicketRecord


def test_ticket_embedding_cache_survives_restart_and_invalidates_changed_text(
    tmp_path, monkeypatch, inject_mock_model
):
    """Unchanged pool tickets must survive restart; one changed ticket is re-embedded."""
    ai_core = Path(__file__).resolve().parent.parent
    fixtures = Path(__file__).resolve().parent / "fixtures"

    config = json.loads(
        (ai_core / "config" / "infrastructure_config.json").read_text(encoding="utf-8")
    )
    ticket_cache_path = tmp_path / "ticket_embeddings.json"
    config["ticket_embeddings"]["cache_path"] = str(ticket_cache_path)
    config["knowledge_base"]["cache_path"] = str(tmp_path / "article_embeddings.json")
    config_path = tmp_path / "infrastructure_config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    monkeypatch.setenv("INFRASTRUCTURE_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("OLD_TICKETS_PATH", str(fixtures / "tickets_small.json"))
    monkeypatch.setenv("KNOWLEDGE_ARTICLES_PATH", str(fixtures / "articles_small.json"))

    batch_calls: list[list[str]] = []
    original_encode_batch = inject_mock_model.encode_batch

    def counted_encode_batch(texts: list[str]) -> list[list[float]]:
        batch_calls.append(list(texts))
        return original_encode_batch(texts)

    inject_mock_model.encode_batch = counted_encode_batch

    first_health = initialize_infrastructure()
    assert first_health.status == "ok"
    assert sum(len(texts) for texts in batch_calls) == 15  # 10 tickets + 5 articles

    persisted = json.loads(ticket_cache_path.read_text(encoding="utf-8"))
    assert len(persisted) == 10
    assert {entry["model_version"] for entry in persisted} == {"mock-v1"}

    # A fresh infrastructure state must reuse both the article and ticket caches.
    batch_calls.clear()
    second_health = initialize_infrastructure()
    assert second_health.status == "ok"
    assert batch_calls == []

    raw_tickets = json.loads((fixtures / "tickets_small.json").read_text(encoding="utf-8"))
    raw_tickets[0]["title"] = "VPN authentication error changed"
    request = InfrastructureRequest(
        ticket_id=99,
        title="VPN cannot connect",
        description="MFA authentication error",
        category="vpn",
        old_tickets=[OldTicketRecord(**record) for record in raw_tickets],
    )

    batch_calls.clear()
    result = run_infrastructure(request)
    assert result.error is None
    assert [len(texts) for texts in batch_calls] == [1]
