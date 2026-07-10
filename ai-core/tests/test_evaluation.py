import json
import logging
from pathlib import Path

from app.infrastructure.evaluation import (
    eval_category_accuracy,
    eval_retrieval_category_accuracy,
)


def test_retrieval_category_accuracy_is_explicit_and_legacy_alias_is_compatible(
    inject_mock_model, caplog
):
    ai_core = Path(__file__).resolve().parent.parent
    config = json.loads(
        (ai_core / "config" / "infrastructure_config.json").read_text(encoding="utf-8")
    )
    eval_set = str(ai_core / "data" / "evaluation_set.json")
    old_tickets = str(ai_core / "data" / "old_tickets.json")

    retrieval_report = eval_retrieval_category_accuracy(
        eval_set,
        old_tickets,
        inject_mock_model,
        config,
    )
    with caplog.at_level(logging.WARNING):
        legacy_report = eval_category_accuracy(
            eval_set,
            old_tickets,
            inject_mock_model,
            config,
        )

    assert retrieval_report.total_evaluated == 60
    assert legacy_report == retrieval_report
    assert any(
        "retrieval metric, not an Analyzer metric" in message
        for message in caplog.messages
    )
