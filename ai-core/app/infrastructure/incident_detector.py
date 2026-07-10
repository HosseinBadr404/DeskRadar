"""
ServiceDesk Radar — AI Infrastructure
app/infrastructure/incident_detector.py  (Step 16)

detect_incident_candidate(): decides whether a cluster of similar tickets in the
same category constitutes a possible operational incident.

Rules (handoff §9.6 / Milestone 4):
  * Inputs are the already-computed list[SimilarTicket] plus the query category
    and config. This module NEVER calls similarity_search.py (Critical Rule 2);
    it only consumes the similar tickets handed to it.
  * Only tickets at/above `incident_detection.similarity_floor` count toward a
    cluster, and (when a category is given) only tickets in that category.
  * Severity bands come from config (Rule 4 — nothing hardcoded):
        count >= high_min_tickets                  -> "high"
        medium_min_tickets <= count <= medium_max  -> "medium"
        otherwise                                  -> no incident
  * Persian title and reason strings are produced and non-empty when an
    incident is flagged.
  * is_duplicate is True only when an open incident in the same category shares
    at least one matched ticket with this cluster. The Backend receives the
    matching incident ID so it can update that record rather than create one.

No analyzer/ import (Rule 5).
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import TYPE_CHECKING

from .schemas import IncidentCandidate, OpenIncidentRecord

if TYPE_CHECKING:  # type-only; SimilarTicket is consumed via attribute access
    from .schemas import SimilarTicket

logger = logging.getLogger(__name__)

# Persian service labels for incident titles/reasons (presentation only).
_SERVICE_LABELS: dict[str, str] = {
    "vpn": "VPN",
    "email": "ایمیل",
    "printer": "پرینتر",
    "network": "شبکه",
    "account": "حساب کاربری",
    "software": "نرم‌افزار",
    "hardware": "سخت‌افزار",
}

_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def detect_incident_candidate(
    similar_tickets: list["SimilarTicket"],
    category: str | None,
    config: dict,
    *,
    open_incidents: list[OpenIncidentRecord] | None = None,
) -> IncidentCandidate:
    """
    Parameters
    ----------
    similar_tickets : top similar tickets from similarity_search (passed in).
    category        : the query ticket's category (optional, from Analyzer).
    config          : full infrastructure config (or its "incident_detection" block).
    open_incidents : open incidents with their category and matched ticket IDs.
                     A candidate is a duplicate only if its cluster overlaps one
                     of these incidents in the same category.

    Returns
    -------
    IncidentCandidate (neutral when no incident is detected; never raises).
    """
    floor, medium_min, medium_max, high_min = _read_incident_config(config)

    # Tickets strong enough to count toward a cluster.
    above_floor = [t for t in (similar_tickets or []) if float(t.similarity) >= floor]

    cluster, cluster_category = _select_cluster(above_floor, category)
    count = len(cluster)

    severity = _severity_for(count, medium_min, medium_max, high_min)
    if severity is None:
        return IncidentCandidate(possible_incident=False)

    avg_score = round(sum(float(t.similarity) for t in cluster) / count, 2)
    matched_ids = [int(t.ticket_id) for t in cluster]
    label = _service_label(cluster_category)

    duplicate_incident_id = _find_duplicate_incident_id(
        cluster_category,
        matched_ids,
        open_incidents,
    )

    return IncidentCandidate(
        possible_incident=True,
        severity=severity,
        fa_title_incident=f"رخداد احتمالی در سرویس {label}",
        fa_reason_incident=(
            f"{_fa(count)} تیکت مشابه با میانگین شباهت {_fa(f'{avg_score:.2f}')} "
            f"در دسته {label} شناسایی شد."
        ),
        matched_ticket_ids=matched_ids,
        avg_similarity_score=avg_score,
        is_duplicate=duplicate_incident_id is not None,
        duplicate_incident_id=duplicate_incident_id,
    )


# ---------------------------------------------------------------------------- #
# Helpers
# ---------------------------------------------------------------------------- #
def _select_cluster(
    above_floor: list["SimilarTicket"], category: str | None
) -> tuple[list["SimilarTicket"], str | None]:
    """
    Choose the cluster of tickets that defines the incident.

    With an explicit category, the cluster is the above-floor tickets in that
    category. Without one, the dominant category among the above-floor tickets
    is used.
    """
    if not above_floor:
        return [], category

    if category:
        cluster = [t for t in above_floor if t.category == category]
        return cluster, category

    counts = Counter(t.category for t in above_floor)
    dominant = counts.most_common(1)[0][0]
    cluster = [t for t in above_floor if t.category == dominant]
    return cluster, dominant


def _severity_for(
    count: int, medium_min: int, medium_max: int, high_min: int
) -> str | None:
    if count >= high_min:
        return "high"
    if medium_min <= count <= medium_max:
        return "medium"
    # Safety for non-contiguous config (e.g. medium_max=3, high_min=5, count=4):
    # still a repeated issue, classified medium.
    if medium_max < count < high_min:
        return "medium"
    return None


def _find_duplicate_incident_id(
    cluster_category: str | None,
    matched_ticket_ids: list[int],
    open_incidents: list[OpenIncidentRecord] | None,
) -> int | None:
    """Return the best matching open incident, never one from an unrelated cluster."""
    if not cluster_category or not matched_ticket_ids or not open_incidents:
        return None

    cluster_ids = set(matched_ticket_ids)
    candidates: list[tuple[int, int]] = []  # (overlap_count, incident_id)
    for incident in open_incidents:
        if incident.category != cluster_category:
            continue
        overlap_count = len(cluster_ids.intersection(incident.matched_ticket_ids))
        if overlap_count:
            candidates.append((overlap_count, incident.incident_id))

    if not candidates:
        return None

    # Prefer the incident with the strongest cluster overlap; resolve a tie by
    # ID for deterministic behaviour.
    return min(candidates, key=lambda item: (-item[0], item[1]))[1]


def _service_label(category: str | None) -> str:
    if not category:
        return "نامشخص"
    return _SERVICE_LABELS.get(category, category)


def _fa(value) -> str:
    """Render a number/string with Persian digits (presentation only)."""
    return str(value).translate(_FA_DIGITS)


def _read_incident_config(config: dict) -> tuple[float, int, int, int]:
    inc = config.get("incident_detection", config)
    return (
        float(inc["similarity_floor"]),
        int(inc["medium_min_tickets"]),
        int(inc["medium_max_tickets"]),
        int(inc["high_min_tickets"]),
    )
