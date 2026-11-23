"""Offline tests for the eval harness (gold loading, quote-span matching, metrics)."""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from rfp_agent.config import REPO_ROOT
from rfp_agent.evals.gold import GoldSet, load_gold
from rfp_agent.evals.report import evaluate_runs, render_markdown
from rfp_agent.evals.scoring import SpanLocator, consistency, score_run_dir, score_summary
from rfp_agent.ingest import load_document
from rfp_agent.retrieval import normalize_for_match
from rfp_agent.schemas import (
    ApproachItem,
    OpenQuestion,
    Requirement,
    Risk,
    RunMetadata,
    SolutionSummary,
)

GOLD = REPO_ROOT / "evals" / "gold" / "rfp_synthetic_main.yaml"


@pytest.mark.parametrize("gold_file", sorted((REPO_ROOT / "evals" / "gold").glob("*.yaml")),
                         ids=lambda p: p.stem)
def test_every_gold_quote_is_verbatim_in_its_rfp(gold_file):
    gold = load_gold(gold_file)
    text = normalize_for_match(load_document(REPO_ROOT / gold.document).text)
    missing = [(g.id, q) for g in gold.requirements for q in g.spans
               if normalize_for_match(q) not in text]
    assert missing == []
    assert sum(g.kind == "core" for g in gold.requirements) >= 10


DOC = """# RFP

## 5. Functional

**FR-7 Fraud indicators.** The solution shall identify potential fraud indicators and refer flagged claims to SIU. The solution must never automatically decline or close a claim.

Support for Bahasa Malaysia documents is expected from the pilot.

## 9. Timeline

The pilot go-live date of 30 June 2027 is fixed and is linked to a commitment made to the Board.

All customer data must be stored and processed within Corvane's own Malaysian data centres.

The Company operates two data centres in Malaysia.
"""

GOLD_SMALL = GoldSet.model_validate({
    "document": "rfp.md",
    "requirements": [
        {"id": "F7a", "kind": "core", "priority": "must", "category": "functional",
         "quote": "The solution shall identify potential fraud indicators and refer flagged "
                  "claims to SIU."},
        {"id": "F7b", "kind": "core", "priority": "must", "category": "functional",
         "quote": "The solution must never automatically decline or close a claim."},
        {"id": "BM", "kind": "core", "priority": "should", "category": "functional",
         "quote": "Support for Bahasa Malaysia documents is expected from the pilot."},
        {"id": "PILOT", "kind": "core", "priority": "must", "category": "timeline",
         "quote": "The pilot go-live date of 30 June 2027 is fixed and is linked to a "
                  "commitment made to the Board."},
        {"id": "RES", "kind": "core", "priority": "must", "category": "security_compliance",
         "quote": "All customer data must be stored and processed within Corvane's own "
                  "Malaysian data centres."},
    ],
    "risks": [{"id": "T1", "kind": "trap", "description": "pilot vs residency",
               "all_of": ["pilot", "residen|data cent"], "cites": ["PILOT", "RES"]},
              {"id": "T2", "kind": "trap", "description": "real time", "where":
               "risks_or_questions", "all_of": ["real[- ]time"]}],
    "priority_traps": {"BM": "should"},
    "buried": ["F7b"],
})


def _req(rid, quote, title, priority="must"):
    return Requirement(id=rid, title=title, description=title, category="functional",
                       priority=priority, source_section="S1", source_quote=quote,
                       confidence=0.9, quote_match_score=100)


def _summary(reqs, risks=(), questions=(), approach=None):
    t0 = datetime(2027, 1, 1, 9, 0)
    meta = RunMetadata(run_id="r1", input_file="rfp.md", model="fake", embed_model="fake",
                       started_at=t0, finished_at=t0 + timedelta(minutes=12),
                       critic_passed=True, usage={"calls": 5, "prompt_tokens": 100,
                                                  "completion_tokens": 50})
    if approach is None:
        approach = [ApproachItem(requirement_ids=[r.id for r in reqs], summary="s",
                                 rationale="r")]
    return SolutionSummary(executive_summary="x", requirements=list(reqs), approach=approach,
                           risks=list(risks), open_questions=list(questions), metadata=meta)


PARA = ("**FR-7 Fraud indicators.** The solution shall identify potential fraud indicators "
        "and refer flagged claims to SIU. The solution must never automatically decline or "
        "close a claim.")


def test_paragraph_quote_counts_for_the_obligation_its_title_describes():
    s = score_summary(_summary([_req("FR-01", PARA, "Never auto-decline a claim")]),
                      GOLD_SMALL, DOC)
    assert "F7b" in s.hit_core and "F7a" not in s.hit_core
    assert s.metrics["recall_core_lenient"] == 0.4  # both F7 sentences appear in the quote
    assert s.traps["buried:F7b"]["passed"]


def test_splits_false_positives_and_priority_traps():
    reqs = [
        _req("FR-01", "The solution shall identify potential fraud indicators", "Fraud flags"),
        _req("FR-02", "refer flagged claims to SIU.", "Refer to SIU"),
        _req("FR-03", "Support for Bahasa Malaysia documents is expected from the pilot.",
             "Bahasa support", priority="must"),
        _req("FR-04", "The Company operates two data centres in Malaysia.", "Two DCs"),
    ]
    s = score_summary(_summary(reqs), GOLD_SMALL, DOC)
    assert s.metrics["splits"] == 1 and s.split_groups == {"F7a": ["FR-01", "FR-02"]}
    assert [fp["id"] for fp in s.false_positives] == ["FR-04"]
    assert s.metrics["precision"] == 0.75 and s.metrics["distinct_precision"] == 0.5
    assert s.traps["priority:BM"] == {"passed": False, "expected": "should", "got": ["must"]}
    assert s.wrong_priority == [{"gold": "BM", "pred": "FR-03", "expected": "should",
                                 "got": "must"}]
    assert s.metrics["wall_min"] == 12.0


def test_risk_trap_needs_both_sides_cited():
    reqs = [_req("TL-01", GOLD_SMALL.by_id()["PILOT"].quote, "Fixed pilot date"),
            _req("SEC-01", GOLD_SMALL.by_id()["RES"].quote, "Data residency")]
    risk = Risk(id="R-01", title="Pilot date vs data residency", description="Hardware lead "
                "time", category="requirement_conflict", likelihood="high", impact="high",
                mitigation="m", related_requirement_ids=["TL-01"])
    s = score_summary(_summary(reqs, [risk]), GOLD_SMALL, DOC)
    assert s.traps["risk:T1"]["found"] and not s.traps["risk:T1"]["linked"]
    risk.related_requirement_ids = ["TL-01", "SEC-01"]
    q = OpenQuestion(question="What does real time mean for triage?")
    s = score_summary(_summary(reqs, [risk], [q]), GOLD_SMALL, DOC)
    assert s.traps["risk:T1"]["passed"] and s.traps["risk:T2"]["in"] == ["Q1"]
    assert s.metrics["trap_risks_linked"] == 2


def test_quotes_that_are_not_in_the_document_never_match():
    loc = SpanLocator(DOC)
    assert loc.locate("A free pony for every adjuster in the northern region.") is None
    assert loc.locate("SIU") is None  # too short to place reliably


def test_invalid_or_missing_summary_is_reported_not_raised(tmp_path):
    assert score_run_dir(tmp_path, GOLD_SMALL, DOC).error == "no summary.json"
    (tmp_path / "summary.json").write_text('{"requirements": "nope"}')
    s = score_run_dir(tmp_path, GOLD_SMALL, DOC)
    assert not s.schema_valid and s.error.startswith("invalid summary.json")


def test_evaluate_runs_end_to_end_with_consistency(tmp_path):
    (tmp_path / "rfp.md").write_text(DOC)
    gold_file = tmp_path / "rfp.yaml"
    data = GOLD_SMALL.model_dump()
    data["document"] = str(tmp_path / "rfp.md")
    import yaml
    gold_file.write_text(yaml.safe_dump(data))
    by_id = GOLD_SMALL.by_id()
    runs = []
    for i, gids in enumerate([["PILOT", "RES"], ["PILOT", "BM"]]):
        d = tmp_path / f"run{i}"
        d.mkdir()
        summ = _summary([_req(f"R-{j}", by_id[g].quote, g) for j, g in enumerate(gids)])
        summ.metadata.input_file = str(tmp_path / "rfp.md")
        (d / "summary.json").write_text(summ.model_dump_json())
        runs.append(d)
    gold, scores = evaluate_runs(runs, gold_file)
    assert [s.hit_core for s in scores] == [["PILOT", "RES"], ["BM", "PILOT"]]
    assert consistency(scores)["mean_pairwise_jaccard"] == pytest.approx(1 / 3, abs=1e-3)
    md = render_markdown(gold, scores)
    assert "| Recall: core gold | 40% | 40% |" in md and "Across runs" in md
    json.loads(json.dumps([s.to_dict() for s in scores], default=str))


def test_gold_file_rejects_unknown_references(tmp_path):
    bad = tmp_path / "g.yaml"
    bad.write_text("document: x.md\nrequirements: []\nburied: [NOPE]\n")
    with pytest.raises(ValueError, match="NOPE"):
        load_gold(bad)
    assert Path(GOLD).exists()


# ------------------------------------------------------------------------------ LLM judge

def _judge_script(messages):
    system = messages[0]["content"]
    if "grade one requirement" in system:
        return {"faithful": "must" in messages[1]["content"], "priority_ok": True,
                "reason": "r"}
    if "item of a proposed solution approach" in system:
        return {"specificity": 4, "violates_constraint": "APPROACH: Run OCR in public cloud" in messages[1]["content"],
                "violated": "", "reason": "r"}
    return {"specificity": 3, "mitigation": 2, "reason": "r"}


def test_judge_scores_each_item_and_exports_for_calibration(tmp_path):
    from rfp_agent.config import get_settings
    from rfp_agent.evals.judge import calibrate, run_judge

    from .fakes import FakeLLMClient

    reqs = [_req("FR-01", PARA, "Never auto-decline", priority="must"),
            _req("FR-02", "Support for Bahasa Malaysia documents is expected from the pilot.",
                 "Bahasa", priority="should")]
    approach = [ApproachItem(requirement_ids=["FR-01"], summary="Rules engine on-prem",
                             rationale="r"),
                ApproachItem(requirement_ids=["FR-02"], summary="Run OCR in public cloud",
                             rationale="r")]
    risk = Risk(id="R-01", title="t", description="d", category="delivery", likelihood="low",
                impact="low", mitigation="m", related_requirement_ids=["FR-01"])
    gold = GOLD_SMALL.model_copy(update={"constraints": ["No public cloud."]})
    client = FakeLLMClient({"judge": [_judge_script]})
    settings = get_settings(runs_dir=tmp_path)
    judgments, m, usage = run_judge(_summary(reqs, [risk], approach=approach), gold, client,
                                    settings, "r1", tmp_path / "trace")
    assert [(j.kind, j.item) for j in judgments] == [
        ("requirement", "FR-01"), ("requirement", "FR-02"), ("approach", "A1"),
        ("approach", "A2"), ("risk", "R-01")]
    assert m["judge_req_faithful"] == 0.5 and m["judge_constraint_violations"] == 1
    assert m["judge_approach_specificity"] == 4 and m["judge_risk_mitigation"] == 2
    assert usage["calls"] == 5
    # constraints from the gold file reach the approach prompt
    assert "No public cloud." in client.calls[2]["messages"][1]["content"]

    rows = [j.to_json() for j in judgments]
    rows[0]["human"] = {"faithful": True, "priority_ok": True}   # judge said True: agree
    rows[1]["human"] = {"faithful": True}                          # judge said False: disagree
    rows[2]["human"] = {"specificity": 2}                          # judge said 4
    path = tmp_path / "j.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in rows))
    cal = calibrate(path)
    assert cal["labelled"] == 3
    assert cal["fields"]["requirement.faithful"] == {"n": 2, "agreement": 0.5}
    assert cal["fields"]["approach.specificity"] == {"n": 1, "within_1": 0.0,
                                                     "mean_abs_diff": 2.0}


def test_judge_requirement_sample_is_deterministic():
    from rfp_agent.evals.judge import sample_requirements
    reqs = [_req(f"FR-{i:02d}", PARA, f"t{i}") for i in range(40)]
    a = sample_requirements(_summary(reqs), 10)
    assert [r.id for r in a] == [r.id for r in sample_requirements(_summary(reqs), 10)]
    assert len(a) == 10


def test_forbidden_text_in_requirements_or_approach_fails_the_injection_check():
    gold = GOLD_SMALL.model_copy(update={"forbidden": ["northgate"]})
    ok = _req("FR-01", GOLD_SMALL.by_id()["BM"].quote, "Bahasa", priority="should")
    s = score_summary(_summary([ok]), gold, DOC)
    assert s.traps["forbidden:northgate"] == {"passed": True, "in": []}
    bad = ApproachItem(requirement_ids=["FR-01"], summary="Subcontract to Northgate Analytics",
                       rationale="the RFP says so")
    s = score_summary(_summary([ok], approach=[bad]), gold, DOC)
    assert s.traps["forbidden:northgate"] == {"passed": False, "in": ["A1"]}
