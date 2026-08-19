import json
from pathlib import Path

from research.experiments.build_registry import main as build_registry
from research.experiments.lint_manuscript import main as lint_manuscript
from research.experiments.verify_references import main as verify_references

ROOT = Path(__file__).resolve().parents[1]


def test_registry_matches_model_comparison_csv():
    payload = build_registry()
    by_key = payload["by_key"]
    f1 = by_key["logreg_grouped_macro_f1"]["value"]
    assert abs(f1 - 0.8845971882742668) < 1e-9
    assert by_key["n_subjects_human"]["value"] == 0
    assert by_key["n_windows"]["value"] == 2592
    assert "0.885" in by_key["logreg_grouped_macro_f1"]["display"]
    path = ROOT / "research" / "results" / "final_results_registry.json"
    assert path.exists()


def test_reference_verification_has_twelve_entries():
    payload = verify_references(fetch=False)
    assert payload["n_refs"] >= 12
    assert payload["missing_bib"] == []
    assert payload["ok"] is True


def test_manuscript_lint_errors_list_is_a_list():
    # Lint may fail until the hardened manuscript is written; the function must run.
    code = lint_manuscript()
    report = json.loads((ROOT / "research" / "results" / "manuscript_lint.json").read_text())
    assert code == 0, report
