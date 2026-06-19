import os
from pathlib import Path
from app.infrastructure import initialize_infrastructure, run_infrastructure
from app.infrastructure.schemas import InfrastructureRequest


def test_pipeline_integration(inject_mock_model):
    # Set environment variables to point to test fixtures
    tests_dir = Path(__file__).resolve().parent
    fixtures_dir = tests_dir / "fixtures"

    os.environ["INFRASTRUCTURE_CONFIG_PATH"] = str(tests_dir.parent / "config" / "infrastructure_config.json")
    os.environ["OLD_TICKETS_PATH"] = str(fixtures_dir / "tickets_small.json")
    os.environ["KNOWLEDGE_ARTICLES_PATH"] = str(fixtures_dir / "articles_small.json")

    try:
        # 1) Initialize the infrastructure (Step 17/19)
        health_status = initialize_infrastructure()
        assert health_status.status == "ok"
        assert health_status.model_loaded is True
        assert health_status.tickets_in_pool == 10
        assert health_status.articles_indexed == 5

        # 2) Run analysis on a new VPN ticket
        # There are 5 existing VPN tickets in tickets_small.json, so it should trigger a high severity incident (>= 4 tickets)
        request = InfrastructureRequest(
            ticket_id=99,
            title="VPN connects fail with auth error",
            description="Cannot login to VPN on Windows 11",
            category="vpn",
            old_tickets=[]  # Empty live pool, since Qdrant is disabled it falls back to the startup seeded pool
        )
        # In __init__.py, when Qdrant is disabled:
        # pool, titles = _embed_records(request.old_tickets, model, config)
        # Wait, if request.old_tickets is empty, let's verify if it defaults to the seed ticket pool!
        # Let's check __init__.py:
        # qa = _active_qdrant()
        # if qa is not None:
        #     pool, titles, qdrant_for_search = _state.seed_ticket_pool, _state.seed_title_lookup, qa
        # else:
        #     try:
        #         pool, titles = _embed_records(request.old_tickets, model, config)
        #     ...
        # Wait! If Qdrant is NOT active, and the caller passes `request.old_tickets=[]`, it embeds `request.old_tickets` (which is empty) and searches over that empty pool!
        # So we should pass the pool in `request.old_tickets` if we want to run Python cosine over it, OR we can mock it.
        # Let's load existing tickets from tickets_small.json and pass them in `request.old_tickets`!
        # Let's check `tickets_small.json` loading.
        import json
        from app.infrastructure.schemas import OldTicketRecord
        with open(fixtures_dir / "tickets_small.json", "r", encoding="utf-8") as f:
            raw_tickets = json.load(f)
        
        request.old_tickets = [OldTicketRecord(**t) for t in raw_tickets]

        result = run_infrastructure(request)

        # Assert results
        assert result.error is None
        assert len(result.similar_tickets) > 0
        
        # Verify similar tickets
        for t in result.similar_tickets:
            assert t.category == "vpn"

        # Verify related article
        assert result.related_article is not None
        assert result.related_article.article_id == 1  # VPN guide

        # Verify incident candidate
        assert result.incident.possible_incident is True
        # Since we have 5 VPN tickets in the pool, count = 5 >= 4 -> high severity
        assert result.incident.severity == "high"
        assert result.incident.is_duplicate is False

    finally:
        # Clean up env variables
        os.environ.pop("INFRASTRUCTURE_CONFIG_PATH", None)
        os.environ.pop("OLD_TICKETS_PATH", None)
        os.environ.pop("KNOWLEDGE_ARTICLES_PATH", None)
