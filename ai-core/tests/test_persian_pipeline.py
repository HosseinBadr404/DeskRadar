import json
from pathlib import Path

from app.infrastructure import initialize_infrastructure, run_infrastructure
from app.infrastructure.schemas import InfrastructureRequest, OldTicketRecord


def test_persian_vpn_and_printer_requests_return_same_topic_results(
    tmp_path, monkeypatch, inject_mock_model
):
    """Taskbook §9.4 acceptance: Persian VPN/printer queries keep their topic."""
    ai_core = Path(__file__).resolve().parent.parent
    config = json.loads(
        (ai_core / "config" / "infrastructure_config.json").read_text(encoding="utf-8")
    )
    config["ticket_embeddings"]["cache_path"] = str(tmp_path / "ticket_embeddings.json")
    config["knowledge_base"]["cache_path"] = str(tmp_path / "article_embeddings.json")
    config_path = tmp_path / "infrastructure_config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    monkeypatch.setenv("INFRASTRUCTURE_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("OLD_TICKETS_PATH", str(ai_core / "data" / "old_tickets.json"))
    monkeypatch.setenv("KNOWLEDGE_ARTICLES_PATH", str(ai_core / "data" / "knowledge_articles.json"))

    raw_tickets = json.loads((ai_core / "data" / "old_tickets.json").read_text(encoding="utf-8"))
    old_tickets = [OldTicketRecord(**record) for record in raw_tickets]

    health = initialize_infrastructure()
    assert health.status == "ok"

    vpn_result = run_infrastructure(
        InfrastructureRequest(
            ticket_id=1001,
            title="اتصال VPN برقرار نمی‌شود",
            description="هنگام ورود خطای احراز هویت نمایش داده می‌شود.",
            old_tickets=old_tickets,
        )
    )
    assert vpn_result.error is None
    assert vpn_result.similar_tickets
    assert {match.category for match in vpn_result.similar_tickets} == {"vpn"}
    assert vpn_result.related_article is not None
    assert vpn_result.related_article.category == "vpn"
    assert vpn_result.incident.possible_incident is True
    assert vpn_result.incident.severity == "high"

    printer_result = run_infrastructure(
        InfrastructureRequest(
            ticket_id=1002,
            title="پرینتر چاپ نمی‌کند",
            description="صف چاپ در صف مانده و هیچ برگه‌ای چاپ نمی‌شود.",
            old_tickets=old_tickets,
        )
    )
    assert printer_result.error is None
    assert printer_result.similar_tickets
    assert {match.category for match in printer_result.similar_tickets} == {"printer"}
    assert printer_result.related_article is not None
    assert printer_result.related_article.category == "printer"
