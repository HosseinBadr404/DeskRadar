"""
ServiceDesk Radar — AI Infrastructure
app/infrastructure/evaluation.py  (Step 18)

OFFLINE evaluation utilities. Three functions measure retrieval quality and
return the Pydantic report models from schemas.py:

  * eval_similarity_quality(...)  -> SimilarityReport
  * eval_threshold_sweep(...)     -> ThresholdReport
  * eval_retrieval_category_accuracy(...) -> CategoryReport

Rule 6 — this module is OFFLINE ONLY. It MAY import from embedding_model,
similarity_search, knowledge_base, incident_detector. It MUST NEVER be imported
by any of them, by __init__.py, or by main.py / the live request path.
Suggested CI guard (must return empty):
    grep -rEn "import evaluation|from .* import .*evaluation" app/infrastructure/
        --include="*.py" | grep -v "evaluation.py"

Design (reviewer B5 spec / Taskbook §9.8):
  * Data: data/similarity_pairs.json (eval_NNN pairs) + data/evaluation_set.json
    (labeled eval tickets) + data/old_tickets.json (retrieval corpus).
  * Pre-flight: every pair id must resolve in the eval set, else ValueError.
  * Eval ticket text is built with category=None (the eval set's expected_category
    is a label, not a text prefix) so similarity reflects title+description only.
  * Callers (the Step 21 script) are responsible for initialize-style setup
    (loading config + model); these functions do NOT call initialize_infrastructure().
"""

from __future__ import annotations

import json
import logging
import math
import os
from collections import Counter
from statistics import mean

from .embedding_model import EmbeddingModel, build_ticket_text
from .schemas import (
    CategoryReport,
    OldTicketRecord,
    SimilarityReport,
    ThresholdReport,
    TicketVectorEntry,
)
from .similarity_search import find_similar_tickets

logger = logging.getLogger(__name__)

_DEFAULT_EVAL_SET_PATH = "data/evaluation_set.json"
_DEFAULT_PAIRS_PATH = "data/similarity_pairs.json"
_DEFAULT_OLD_TICKETS_PATH = "data/old_tickets.json"

# Default sweep grid (reviewer B5; superset of the Taskbook §9.8 values).
_DEFAULT_THRESHOLDS = [0.65, 0.70, 0.75, 0.78, 0.80, 0.82, 0.85]


# ---------------------------------------------------------------------------- #
# Public eval functions
# ---------------------------------------------------------------------------- #
def eval_similarity_quality(
    eval_set_path: str = _DEFAULT_EVAL_SET_PATH,
    pairs_path: str = _DEFAULT_PAIRS_PATH,
    model: EmbeddingModel | None = None,
    config: dict | None = None,
) -> SimilarityReport:
    """
    Compare cosine scores of ground-truth similar vs dissimilar pairs.

    pass: similar pair scores >= threshold_similar; dissimilar pair scores < it.
    recommended_threshold = midpoint of the two average scores (2 dp).
    """
    model = model or EmbeddingModel.instance()
    threshold_similar = _threshold_similar(config)

    index = _load_eval_index(eval_set_path)
    pairs = _load_pairs(pairs_path)
    _assert_pairs_resolve(pairs, index)

    similar_scores, dissimilar_scores = _score_pairs(pairs, index, model)
    total_pairs = len(similar_scores) + len(dissimilar_scores)

    similar_avg = _mean(similar_scores)
    dissimilar_avg = _mean(dissimilar_scores)
    separation_gap = round(similar_avg - dissimilar_avg, 4)

    passing = sum(1 for s in similar_scores if s >= threshold_similar)
    passing += sum(1 for s in dissimilar_scores if s < threshold_similar)
    pass_rate = round(passing / total_pairs, 4) if total_pairs else 0.0

    recommended = round((similar_avg + dissimilar_avg) / 2, 2)

    return SimilarityReport(
        total_pairs=total_pairs,
        similar_pairs_avg_score=round(similar_avg, 4),
        dissimilar_pairs_avg_score=round(dissimilar_avg, 4),
        separation_gap=separation_gap,
        pass_rate=pass_rate,
        recommended_threshold=recommended,
    )


def eval_threshold_sweep(
    eval_set_path: str = _DEFAULT_EVAL_SET_PATH,
    pairs_path: str = _DEFAULT_PAIRS_PATH,
    model: EmbeddingModel | None = None,
    config: dict | None = None,
    thresholds: list[float] | None = None,
) -> ThresholdReport:
    """
    For each candidate threshold, compute the fraction of pairs classified
    correctly (similar >= t, dissimilar < t). Recommend the threshold with the
    highest pass rate; ties resolve to the HIGHER threshold (more conservative).
    """
    model = model or EmbeddingModel.instance()
    tested = sorted(thresholds or _DEFAULT_THRESHOLDS)

    index = _load_eval_index(eval_set_path)
    pairs = _load_pairs(pairs_path)
    _assert_pairs_resolve(pairs, index)

    similar_scores, dissimilar_scores = _score_pairs(pairs, index, model)
    total = len(similar_scores) + len(dissimilar_scores)

    pass_rates: list[float] = []
    for t in tested:
        if total == 0:
            pass_rates.append(0.0)
            continue
        correct = sum(1 for s in similar_scores if s >= t)
        correct += sum(1 for s in dissimilar_scores if s < t)
        pass_rates.append(round(correct / total, 4))

    recommended = _argmax_threshold(tested, pass_rates)

    return ThresholdReport(
        tested_thresholds=tested,
        pass_rates=pass_rates,
        recommended_threshold=recommended,
    )


def eval_retrieval_category_accuracy(
    eval_set_path: str = _DEFAULT_EVAL_SET_PATH,
    old_tickets_path: str = _DEFAULT_OLD_TICKETS_PATH,
    model: EmbeddingModel | None = None,
    config: dict | None = None,
) -> CategoryReport:
    """
    Measure retrieval-derived category accuracy, not the separate Analyzer model.
    For each eval ticket, retrieve similar tickets from the FULL old_tickets pool
    and predict its category by majority vote among the returned SimilarTickets
    (tie-break: category of the highest-scoring ticket). Compare to expected_category.
    """
    model = model or EmbeddingModel.instance()
    if config is None:
        raise ValueError(
            "eval_retrieval_category_accuracy requires config (similarity thresholds, top_k)."
        )

    eval_tickets = _load_eval_list(eval_set_path)
    pool, title_lookup = _build_pool(old_tickets_path, model)

    # Encode all eval queries once (category=None — labels are not text prefixes).
    texts = [build_ticket_text(t["title"], t["description"], None) for t in eval_tickets]
    query_vectors = model.encode_batch(texts) if texts else []

    total = 0
    correct = 0
    per_cat_total: Counter = Counter()
    per_cat_correct: Counter = Counter()

    for ticket, qvec in zip(eval_tickets, query_vectors):
        expected = ticket["expected_category"]
        similar = find_similar_tickets(qvec, pool, config, title_lookup=title_lookup)
        predicted = _majority_category(similar)

        total += 1
        per_cat_total[expected] += 1
        if predicted == expected:
            correct += 1
            per_cat_correct[expected] += 1

    accuracy = round(correct / total, 4) if total else 0.0
    per_category = {
        cat: round(per_cat_correct[cat] / per_cat_total[cat], 4)
        for cat in per_cat_total
    }

    return CategoryReport(
        total_evaluated=total,
        correct=correct,
        accuracy=accuracy,
        per_category=per_category,
    )


def eval_category_accuracy(
    eval_set_path: str = _DEFAULT_EVAL_SET_PATH,
    old_tickets_path: str = _DEFAULT_OLD_TICKETS_PATH,
    model: EmbeddingModel | None = None,
    config: dict | None = None,
) -> CategoryReport:
    """Backward-compatible alias; use eval_retrieval_category_accuracy instead."""
    logger.warning(
        "eval_category_accuracy is a retrieval metric, not an Analyzer metric; "
        "use eval_retrieval_category_accuracy instead."
    )
    return eval_retrieval_category_accuracy(
        eval_set_path,
        old_tickets_path,
        model,
        config,
    )


# ---------------------------------------------------------------------------- #
# Pair scoring
# ---------------------------------------------------------------------------- #
def _score_pairs(
    pairs: dict, index: dict[str, dict], model: EmbeddingModel
) -> tuple[list[float], list[float]]:
    """Encode each referenced eval ticket once, then cosine-score every pair."""
    referenced: set[str] = set()
    for group in ("similar_pairs", "dissimilar_pairs"):
        for p in pairs.get(group, []):
            referenced.add(p["ticket_a"])
            referenced.add(p["ticket_b"])

    ordered_ids = sorted(referenced)
    texts = [
        build_ticket_text(index[i]["title"], index[i]["description"], None)
        for i in ordered_ids
    ]
    vectors = model.encode_batch(texts) if texts else []
    vec_by_id = dict(zip(ordered_ids, vectors))

    similar_scores = [
        _cosine(vec_by_id[p["ticket_a"]], vec_by_id[p["ticket_b"]])
        for p in pairs.get("similar_pairs", [])
    ]
    dissimilar_scores = [
        _cosine(vec_by_id[p["ticket_a"]], vec_by_id[p["ticket_b"]])
        for p in pairs.get("dissimilar_pairs", [])
    ]
    return similar_scores, dissimilar_scores


def _majority_category(similar: list) -> str | None:
    """Most common category among similar tickets; tie-break = highest-scoring."""
    if not similar:
        return None
    counts = Counter(s.category for s in similar)
    max_count = max(counts.values())
    tied = {c for c, n in counts.items() if n == max_count}
    for s in similar:  # similar is sorted by descending similarity
        if s.category in tied:
            return s.category
    return None


# ---------------------------------------------------------------------------- #
# Loading / validation (Rule 7: skip invalid + WARNING)
# ---------------------------------------------------------------------------- #
def _read_json(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_eval_list(path: str) -> list[dict]:
    raw = _read_json(path)
    if not isinstance(raw, list):
        raise ValueError(f"{path} must be a JSON array of eval tickets.")
    out: list[dict] = []
    required = ("ticket_id", "title", "description", "expected_category")
    for rec in raw:
        if not isinstance(rec, dict) or any(k not in rec for k in required):
            logger.warning("Skipping invalid eval ticket: %r", rec)
            continue
        out.append(rec)
    logger.info("Loaded %d eval tickets from %s.", len(out), path)
    return out


def _load_eval_index(path: str) -> dict[str, dict]:
    return {t["ticket_id"]: t for t in _load_eval_list(path)}


def _load_pairs(path: str) -> dict:
    raw = _read_json(path)
    if not isinstance(raw, dict):
        raise ValueError(f"{path} must be a JSON object with similar/dissimilar pairs.")
    pairs = {"similar_pairs": [], "dissimilar_pairs": []}
    for group in pairs:
        for p in raw.get(group, []):
            if isinstance(p, dict) and "ticket_a" in p and "ticket_b" in p:
                pairs[group].append(p)
            else:
                logger.warning("Skipping invalid %s entry: %r", group, p)
    logger.info(
        "Loaded %d similar + %d dissimilar pairs from %s.",
        len(pairs["similar_pairs"]), len(pairs["dissimilar_pairs"]), path,
    )
    return pairs


def _assert_pairs_resolve(pairs: dict, index: dict[str, dict]) -> None:
    """Pre-flight: every pair id must exist in the eval set, else ValueError."""
    missing: set[str] = set()
    for group in ("similar_pairs", "dissimilar_pairs"):
        for p in pairs.get(group, []):
            for key in ("ticket_a", "ticket_b"):
                if p[key] not in index:
                    missing.add(p[key])
    if missing:
        raise ValueError(
            f"similarity_pairs references {len(missing)} id(s) absent from the "
            f"evaluation set: {sorted(missing)}"
        )


def _build_pool(
    old_tickets_path: str, model: EmbeddingModel
) -> tuple[list[TicketVectorEntry], dict[int, str]]:
    """Load + validate old tickets and embed them into the retrieval corpus."""
    raw = _read_json(old_tickets_path)
    records: list[OldTicketRecord] = []
    for rec in raw if isinstance(raw, list) else []:
        try:
            records.append(OldTicketRecord(**rec))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Skipping invalid old-ticket record (%s): %r", exc, rec)

    texts = [build_ticket_text(r.title, r.description, r.category) for r in records]
    vectors = model.encode_batch(texts) if texts else []

    pool = [
        TicketVectorEntry(
            ticket_id=r.ticket_id, vector=v, category=r.category, status=r.status
        )
        for r, v in zip(records, vectors)
    ]
    title_lookup = {r.ticket_id: r.title for r in records}
    logger.info("Built retrieval corpus of %d tickets from %s.", len(pool), old_tickets_path)
    return pool, title_lookup


# ---------------------------------------------------------------------------- #
# Helpers
# ---------------------------------------------------------------------------- #
def _threshold_similar(config: dict | None) -> float:
    if config is None:
        raise ValueError("config is required (similarity.threshold_similar).")
    sim = config.get("similarity", config)
    return float(sim["threshold_similar"])


def _argmax_threshold(tested: list[float], pass_rates: list[float]) -> float:
    best_t = tested[0]
    best_rate = pass_rates[0]
    for t, rate in zip(tested, pass_rates):
        if rate > best_rate or (rate == best_rate and t > best_t):
            best_rate, best_t = rate, t
    return best_t


def _mean(values: list[float]) -> float:
    return float(mean(values)) if values else 0.0


def _cosine(a: list[float], b: list[float]) -> float:
    # Local copy (offline module); identical formula to similarity_search /
    # knowledge_base: dot/(norm*norm) clamped to [0, 1].
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = na = nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0.0 or nb == 0.0:
        return 0.0
    sim = dot / (math.sqrt(na) * math.sqrt(nb))
    return 0.0 if sim < 0.0 else 1.0 if sim > 1.0 else sim
