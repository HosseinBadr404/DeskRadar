import re
from pathlib import Path


def test_rule_6_evaluation_import_guard():
    """
    Ensure that `evaluation.py` is never imported by any of the live path files
    in `app/infrastructure/`. (Rule 6: offline evaluation only).
    """
    infra_dir = Path(__file__).resolve().parent.parent / "app" / "infrastructure"
    assert infra_dir.exists()

    import_pattern = re.compile(r"(import\s+evaluation|from\s+.*\s+import\s+.*evaluation)")

    for path in infra_dir.glob("*.py"):
        if path.name == "evaluation.py":
            continue

        content = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(content.splitlines(), start=1):
            # Ignore comments
            clean_line = line.split("#")[0].strip()
            if import_pattern.search(clean_line):
                raise AssertionError(
                    f"Forbidden import of 'evaluation' found in live file {path.name}:{line_no}:\n{line}"
                )
