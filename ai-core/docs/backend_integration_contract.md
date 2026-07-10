# AI Infrastructure - Backend Integration Contract

## Scope and current mode

This contract covers the standalone AI Infrastructure service at `POST /analyze-ticket`.
It returns similarity, knowledge-base retrieval, and incident-candidate data only.
The current demo mode is **Python cosine with `qdrant.enabled=false`**.

The Analyzer and the final combined `analysis + intelligence + meta` response are
separate integration work. Until that combined endpoint exists, the Backend may
call this endpoint and merge the returned infrastructure block itself.

## Request

The Backend must send the current ticket plus the relevant ticket pool on every
request. In default Python mode, the startup seed pool is not searched.

```json
{
  "ticket_id": 101,
  "title": "VPN وصل نمی‌شود",
  "description": "خطای احراز هویت نمایش داده می‌شود.",
  "category": "vpn",
  "old_tickets": [
    {
      "ticket_id": 18,
      "title": "VPN خطا می‌دهد",
      "description": "...",
      "category": "vpn",
      "status": "open"
    }
  ],
  "open_incidents": [
    {
      "incident_id": 7,
      "category": "vpn",
      "matched_ticket_ids": [18, 22, 35]
    }
  ]
}
```

`old_tickets` must include each ticket's current title, description, category,
and status. The service ignores `closed` and `deleted` tickets in similarity
results.

`open_incidents` contains only open incidents. It is required for incident
deduplication. A category alone is not sufficient: the Backend must persist and
send the incident's `matched_ticket_ids`.

## Response and persistence rules

```json
{
  "similar_tickets": [{"ticket_id": 18, "similarity": 0.91}],
  "related_article": {"article_id": 1, "title": "...", "score": 0.88},
  "incident": {
    "possible_incident": true,
    "severity": "high",
    "matched_ticket_ids": [18, 22, 35, 41],
    "is_duplicate": true,
    "duplicate_incident_id": 7
  },
  "embedding_model_version": "multilingual-MiniLM-L12-v2-v1",
  "latency_ms": 340.5,
  "error": null
}
```

Backend responsibilities:

1. Persist `similar_tickets` and `related_article` with the ticket analysis.
2. When `incident.possible_incident=false`, do not create an incident.
3. When `is_duplicate=true`, update `duplicate_incident_id` and merge the new
   matched ticket IDs; do not create a second incident.
4. When `is_duplicate=false`, create a new incident and persist its category and
   `matched_ticket_ids` for the next request.
5. When `error` is non-null, retain any successful partial fields and set the
   analysis status to `partial`; for transport failure, set it to `failed`.

## Acceptance flow

1. Create a Persian VPN ticket with a pool containing at least four similar open
   VPN tickets.
2. Confirm the response includes VPN similars, a VPN article, and a high incident.
3. Persist that incident with its matched ticket IDs.
4. Create another ticket from the same cluster and send the persisted open
   incident context.
5. Confirm `is_duplicate=true` and `duplicate_incident_id` points to the first
   incident instead of creating another record.
