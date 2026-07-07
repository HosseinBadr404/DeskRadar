import json
from pathlib import Path
from app.infrastructure.schemas import OldTicketRecord, TicketVectorEntry
from app.infrastructure.similarity_search import find_similar_tickets
from app.infrastructure.embedding_model import build_ticket_text


def load_small_pool(model):
    fixture_path = Path(__file__).resolve().parent / "fixtures" / "tickets_small.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    pool = []
    title_lookup = {}
    for item in data:
        record = OldTicketRecord(**item)
        text = build_ticket_text(record.title, record.description, record.category)
        vector = model.encode(text)
        pool.append(
            TicketVectorEntry(
                ticket_id=record.ticket_id,
                vector=vector,
                category=record.category,
                status=record.status,
            )
        )
        title_lookup[record.ticket_id] = record.title
    return pool, title_lookup


def test_find_similar_tickets(inject_mock_model):
    pool, title_lookup = load_small_pool(inject_mock_model)
    config = {
        "similarity": {
            "top_k": 5,
            "threshold_similar": 0.70,
            "threshold_very_similar": 0.85,
        }
    }

    # Query for a VPN ticket
    query_text = "VPN connected fails with login error"
    query_vector = inject_mock_model.encode(query_text)

    similar = find_similar_tickets(
        query_vector,
        pool,
        config,
        query_ticket_id=99,
        title_lookup=title_lookup,
    )

    # All VPN tickets in tickets_small.json (IDs 1, 2, 3, 4, 5) should match (similarity ~ 1.0)
    # and they should be in the top results. Printer tickets (IDs 6, 7, 8, 9, 10) have similarity ~ 0.0 and should be filtered out.
    assert len(similar) > 0
    for match in similar:
        assert match.category == "vpn"
        assert match.similarity >= 0.70
        assert match.match_level in ("similar", "very_similar")


def test_self_match_guard(inject_mock_model):
    pool, title_lookup = load_small_pool(inject_mock_model)
    config = {
        "similarity": {
            "top_k": 5,
            "threshold_similar": 0.70,
            "threshold_very_similar": 0.85,
        }
    }

    # Query using Ticket 1's content
    query_vector = pool[0].vector
    similar = find_similar_tickets(
        query_vector,
        pool,
        config,
        query_ticket_id=1,  # Guarding ticket_id = 1
        title_lookup=title_lookup,
    )

    # Ticket 1 must not be in the results
    matched_ids = [t.ticket_id for t in similar]
    assert 1 not in matched_ids


def test_deleted_closed_filter(inject_mock_model):
    pool, title_lookup = load_small_pool(inject_mock_model)
    config = {
        "similarity": {
            "top_k": 5,
            "threshold_similar": 0.70,
            "threshold_very_similar": 0.85,
        }
    }

    # Mark some VPN tickets as closed or deleted
    pool[0].status = "closed"  # Ticket 1
    pool[1].status = "deleted"  # Ticket 2

    query_text = "VPN authentication problem"
    query_vector = inject_mock_model.encode(query_text)

    similar = find_similar_tickets(
        query_vector,
        pool,
        config,
        query_ticket_id=99,
        title_lookup=title_lookup,
    )

    matched_ids = [t.ticket_id for t in similar]
    assert 1 not in matched_ids
    assert 2 not in matched_ids
