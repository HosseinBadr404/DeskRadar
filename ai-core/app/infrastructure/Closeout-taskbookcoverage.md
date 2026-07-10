# ServiceDesk Radar — AI Infrastructure: Close-Out & Taskbook Coverage

**Scope of this work:** `ai-core/app/infrastructure/` and its config/data/scripts —
i.e. the **Infrastructure Intelligence AI** (Taskbook §9), plus the infrastructure
portions of Core-AI API (§10) and seed/KB data (§11). Everything else in the
Taskbook (Frontend §5, Backend §6, Database §7, Analyzer AI §8, DevOps §12, QA §13)
is **out of scope** and owned by other team members.

Status: **all 21 roadmap steps implemented and self-validated**, with the reviewer's
Critical/High fixes folded in.

---

## 1. Taskbook §9 — Infrastructure Intelligence AI (OUR SCOPE)

### §9.3 Embedding Pipeline
| Taskbook task | Status | Where |
|---|---|---|
| Load embedding model once at startup | ✅ | `embedding_model.py` (singleton, loaded in startup) |
| Build standardized ticket text | ✅ | `build_ticket_text()` |
| Encode new ticket → vector | ✅ | `EmbeddingModel.encode()` / `encode_batch()` |
| Store embedding (don't re-embed unless text changes) | ✅ | persistent article and ticket-vector caches, keyed by text hash + model version |
| Record `embedding_model_version` | ✅ | `model_version` → `InfrastructureResult` / health |

### §9.4 Similar Ticket Search
| Taskbook task | Status | Where |
|---|---|---|
| `find_similar_tickets` → top-5 sorted | ✅ | `similarity_search.py` |
| Filter deleted/closed tickets | ✅ | `EXCLUDED_STATUSES` |
| Store similarity score | ✅ | `SimilarTicket.similarity` |
| Threshold from config | ✅ | `similarity.threshold_similar` / `threshold_very_similar` |
| Self-match guard | ✅ | `query_ticket_id` excluded |
| Test with Persian dataset | ✅ | `test_persian_pipeline.py` validates VPN and printer requests over the full Persian dataset |

### §9.5 Knowledge Base Retrieval
| Taskbook task | Status | Where |
|---|---|---|
| Article structure + ≥10 seed articles | ✅ | `data/knowledge_articles.json` (11) |
| Build article embeddings | ✅ | `build_article_embeddings()` |
| `find_related_article` (VPN→VPN) | ✅ | `knowledge_base.py` |
| Apply minimum score floor | ✅ | `article_score_min` |
| Connect to suggested reply | ✅ (interface) | returns `RelatedArticle.title`; reply-builder wiring is Analyzer-side |

### §9.6 Incident Candidate Detection
| Taskbook task | Status | Where |
|---|---|---|
| Incident rule (count/category/score/severity) | ✅ | `incident_detector.py` |
| Detect medium (2–3) | ✅ | config bands |
| Detect high (≥4) | ✅ | config bands |
| Persian incident title | ✅ | `fa_title_incident` |
| Persian incident reason | ✅ | `fa_reason_incident` (Persian digits) |
| Avoid duplicate incident | ✅ | cluster-overlap dedup via `open_incidents`, returning `duplicate_incident_id` |

### §9.7 Qdrant (optional)
| Taskbook task | Status | Where |
|---|---|---|
| Qdrant service in Docker | ➖ DevOps §12 | adapter ready; compose is DevOps scope |
| Create `tickets` collection | ✅ | `ensure_collections()` |
| Upsert tickets | ✅ | `upsert()` (+ orchestrator seed upsert) |
| Search in Qdrant | ✅ | `search()` + similarity/KB Qdrant paths |
| Fallback without Qdrant | ✅ | Python cosine default (Rule 8) |

### §9.8 Evaluation & Threshold Tuning
| Taskbook task | Status | Where |
|---|---|---|
| `evaluation_set.json` (≥50) | ✅ | 60 labeled tickets |
| Similarity ground truth | ✅ | `similarity_pairs.json` (23+22) |
| Retrieval category accuracy | ✅ | `eval_retrieval_category_accuracy()`; Analyzer accuracy is a joint integration metric |
| Similarity quality | ✅ | `eval_similarity_quality()` |
| Choose final threshold | ✅ | `eval_threshold_sweep()` |
| Quality report for README / `docs/evaluation.md` | ✅ | `scripts/evaluate_infrastructure.py` |

### §10 Core-AI API (infrastructure portion)
| Taskbook task | Status | Where |
|---|---|---|
| `POST /analyze-ticket` (infra block) | ✅ | `app/main.py` → `run_infrastructure` |
| `GET /health` | ✅ | `app/main.py` (200 ok/degraded, 503 error) |
| Model loaded at startup, not per request | ✅ | lifespan + singleton |
| Latency captured | ✅ | `latency_ms` |
| Controlled model errors (no raw exception to Backend) | ✅ | never-raise contract |
| `TicketAnalysisRequest/Response` (combined analyzer+infra) | ➖ Core/Analyzer | combination layer is outside infra scope |

---

## 2. Remaining — IN SCOPE (small follow-ups)

1. **`requirements.txt`** — ✅ now added.
2. **Test suite** — ✅ cache persistence, Persian VPN/printer, error responses, config validation, and Rule 6 are covered by `pytest`.
3. **Real-model evaluation** — ✅ `docs/evaluation.md` was regenerated; separation gap is `0.5914` (> `0.15`) and retrieval category accuracy is `0.9333`.
4. **Qdrant parity** — deferred while `qdrant.enabled=false`; required before Qdrant is enabled.
5. **Place files at repo paths** — the deliverables here are flat-named; map them to the tree in §4 below.

## 3. Remaining — OUT OF SCOPE (other owners, for full-picture awareness)

- **§5 Frontend** (Next.js dashboard) — entirely remaining.
- **§6 Backend** (FastAPI: routes, services, repositories, AIClient, WebSocket, CSV import) — entirely remaining.
- **§7 Database** (PostgreSQL models, migrations, enums, indexes) — remaining.
- **§8 Analyzer AI** (Persian text analysis sub-module) — remaining (separate AI component).
- **§10 Core-AI combination** — the endpoint that merges Analyzer + Infrastructure into the unified `TicketAnalysisResponse`. Our `main.py` provides the guarded hook; the merge layer + Analyzer are remaining.
- **§11 `tickets_sample.csv`** (100-ticket CSV for Backend import) — QA/Data scope (distinct from our `old_tickets.json`).
- **§12 DevOps** — Dockerfiles, `docker-compose.yml` (incl. Qdrant/Redis services), Makefile, per-service `.env`.
- **§13 QA** — cross-layer tests, demo scenario, manual checklists.

---

## 4. File inventory (deliverables → repo paths)

| # | Deliverable file (flat output name) | Place at repo path |
|---|---|---|
| 1 | `infrastructure_config.json` | `ai-core/config/infrastructure_config.json` |
| 2 | `.env.example` | `ai-core/.env.example` |
| 3 | `schemas.py` | `ai-core/app/infrastructure/schemas.py` |
| 4 | `knowledge_articles.json` | `ai-core/data/knowledge_articles.json` |
| 5 | `old_tickets.json` | `ai-core/data/old_tickets.json` |
| 6 | `evaluation_set.json` | `ai-core/data/evaluation_set.json` |
| 7 | `similarity_pairs.json` | `ai-core/data/similarity_pairs.json` |
| 8 | `tickets_small.json` | `ai-core/tests/fixtures/tickets_small.json` |
| 9 | `articles_small.json` | `ai-core/tests/fixtures/articles_small.json` |
| 10 | `similarity_pairs_small.json` | `ai-core/tests/fixtures/similarity_pairs_small.json` |
| 11 | `vpn_incident_scenario.json` | `ai-core/tests/fixtures/vpn_incident_scenario.json` |
| 12 | `embedding_model.py` | `ai-core/app/infrastructure/embedding_model.py` |
| 13 | `qdrant_adapter.py` | `ai-core/app/infrastructure/qdrant_adapter.py` |
| 14 | `similarity_search.py` | `ai-core/app/infrastructure/similarity_search.py` |
| 15 | `knowledge_base.py` | `ai-core/app/infrastructure/knowledge_base.py` |
| 16 | `incident_detector.py` | `ai-core/app/infrastructure/incident_detector.py` |
| 17 | `__init__.py` | `ai-core/app/infrastructure/__init__.py` |
| 18 | `evaluation.py` | `ai-core/app/infrastructure/evaluation.py` |
| 19 | `main.py` | `ai-core/app/main.py` |
| 20 | `seed_embeddings.py` | `ai-core/scripts/seed_embeddings.py` |
| 21 | `evaluate_infrastructure.py` | `ai-core/scripts/evaluate_infrastructure.py` |
| + | `requirements.txt` | `ai-core/requirements.txt` |
| + | `README.md` | `ai-core/README.md` |
| (gen) | `docs/evaluation.md` | written by script |

> Reminder: `app/infrastructure/` also needs an Analyzer-free sibling — there is no
> `app/__init__.py` in this deliverable set; add an empty one so `app` is a package.

---

## 5. Commit checklist

- [ ] Place all files at the repo paths above; add empty `ai-core/app/__init__.py`.
- [ ] `pip install -r requirements.txt` succeeds on a clean env.
- [ ] `python scripts/seed_embeddings.py` builds `data/.cache/article_embeddings.json`.
- [ ] `uvicorn app.main:app` starts; `GET /health` returns `ok`; `/docs` renders.
- [ ] `POST /analyze-ticket` with a VPN ticket returns VPN similars + VPN article + a high incident on the seeded VPN cluster.
- [ ] `python scripts/evaluate_infrastructure.py` writes `docs/evaluation.md`.
- [ ] `separation_gap > 0.15` in the report (else revise dissimilar pairs).
- [ ] Add CI grep guard for Rule 6.
- [ ] `.gitignore` covers `.model_cache/` and `data/.cache/`.

---

## 6. Open verification items (need the real model / runtime)

1. **Separation gap** — ✅ real-model result is `0.5914` (> `0.15`).
2. **Cache-on-second-startup** — ✅ covered by deterministic ticket/article cache tests; recheck after deployment configuration changes.
3. **Qdrant parity** (only if enabling Qdrant) — deferred while Qdrant remains disabled.
4. **Latency** — confirm per-request `latency_ms` is acceptable on the target VPS.
