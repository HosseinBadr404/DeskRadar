from app.infrastructure.schemas import SimilarTicket
from app.infrastructure.incident_detector import detect_incident_candidate


def test_incident_severity_and_counts():
    config = {
        "incident_detection": {
            "similarity_floor": 0.75,
            "medium_min_tickets": 2,
            "medium_max_tickets": 3,
            "high_min_tickets": 4,
        }
    }

    # Case 1: High severity (>= 4 tickets)
    similar_high = [
        SimilarTicket(ticket_id=1, similarity=0.85, match_level="very_similar", title="VPN fails", category="vpn"),
        SimilarTicket(ticket_id=2, similarity=0.80, match_level="similar", title="VPN offline", category="vpn"),
        SimilarTicket(ticket_id=3, similarity=0.79, match_level="similar", title="Cannot connect VPN", category="vpn"),
        SimilarTicket(ticket_id=4, similarity=0.78, match_level="similar", title="VPN down", category="vpn"),
    ]
    candidate_high = detect_incident_candidate(similar_high, "vpn", config)
    assert candidate_high.possible_incident is True
    assert candidate_high.severity == "high"
    assert candidate_high.fa_title_incident == "رخداد احتمالی در سرویس VPN"
    # Ensure Persian digits translation is correct
    assert "۴" in candidate_high.fa_reason_incident
    assert candidate_high.is_duplicate is False

    # Case 2: Medium severity (2-3 tickets)
    similar_med = [
        SimilarTicket(ticket_id=1, similarity=0.85, match_level="very_similar", title="VPN fails", category="vpn"),
        SimilarTicket(ticket_id=2, similarity=0.80, match_level="similar", title="VPN offline", category="vpn"),
    ]
    candidate_med = detect_incident_candidate(similar_med, "vpn", config)
    assert candidate_med.possible_incident is True
    assert candidate_med.severity == "medium"
    assert "۲" in candidate_med.fa_reason_incident

    # Case 3: No incident (< 2 tickets)
    similar_none = [
        SimilarTicket(ticket_id=1, similarity=0.85, match_level="very_similar", title="VPN fails", category="vpn"),
    ]
    candidate_none = detect_incident_candidate(similar_none, "vpn", config)
    assert candidate_none.possible_incident is False


def test_open_incident_duplicates():
    config = {
        "incident_detection": {
            "similarity_floor": 0.75,
            "medium_min_tickets": 2,
            "medium_max_tickets": 3,
            "high_min_tickets": 4,
        }
    }

    similar = [
        SimilarTicket(ticket_id=1, similarity=0.85, match_level="very_similar", title="VPN fails", category="vpn"),
        SimilarTicket(ticket_id=2, similarity=0.80, match_level="similar", title="VPN offline", category="vpn"),
    ]

    # When "vpn" is in open_incident_categories -> is_duplicate must be True
    candidate = detect_incident_candidate(
        similar,
        "vpn",
        config,
        open_incident_categories={"vpn"},
    )
    assert candidate.possible_incident is True
    assert candidate.is_duplicate is True

    # When "vpn" is not in open_incident_categories -> is_duplicate must be False
    candidate_other = detect_incident_candidate(
        similar,
        "vpn",
        config,
        open_incident_categories={"email"},
    )
    assert candidate_other.possible_incident is True
    assert candidate_other.is_duplicate is False
