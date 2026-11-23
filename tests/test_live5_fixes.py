"""Regression tests for the fixes made after live run 5 (failure log F14-F17)."""

from pathlib import Path

from rfp_agent.agents import architect, extractor
from rfp_agent.config import get_settings
from rfp_agent.context import RunContext
from rfp_agent.ingest import load_document
from rfp_agent.schemas import ApproachItem, Requirement
from rfp_agent.tracing import Tracer

from .fakes import FakeLLMClient

RFP = """# RFP

## 6. Non-Functional Requirements

**NFR-3 Availability.** The platform shall be available 99.5% during business hours. Planned maintenance must be scheduled outside these hours.

## 12. Evaluation Criteria

Solution fit will be weighted at 40%.

## 13. Submission Instructions

Proposals should contain:

1. An executive summary of no more than two pages.
2. A requirements compliance matrix responding to every FR, NFR, INT and SEC requirement.
"""


def _doc(tmp_path: Path):
    p = tmp_path / "rfp.md"
    p.write_text(RFP)
    return load_document(p)


def _sid(doc, prefix):
    return next(s.id for s in doc.sections if s.title.startswith(prefix))


def _req(rid, quote, section, priority="must", category="non_functional"):
    return Requirement(id=rid, title=rid, description=rid, category=category, priority=priority,
                       source_section=section, source_quote=quote, confidence=0.9)


def _ctx(tmp_path, client):
    return RunContext(settings=get_settings(runs_dir=tmp_path), client=client,
                      tracer=Tracer("t", tmp_path / "t"))


def test_stitched_label_and_list_quotes_are_rescued_to_exact_spans(tmp_path):
    doc = _doc(tmp_path)
    nfr, sub = _sid(doc, "6."), _sid(doc, "13.")
    label = extractor.ground(_req("A", "**NFR-3 Availability.** Planned maintenance must be "
                                  "scheduled outside these hours.", nfr), doc, 90)
    assert label.source_quote == "Planned maintenance must be scheduled outside these hours."
    assert label.quote_match_score == 100
    listed = extractor.ground(_req("B", "Proposals should contain: 2. A requirements compliance "
                                   "matrix responding to every FR, NFR, INT and SEC requirement.",
                                   sub), doc, 90)
    assert listed.source_quote.startswith("A requirements compliance matrix")
    assert listed.quote_match_score >= 90


def test_rescue_does_not_ground_hallucinations(tmp_path):
    doc = _doc(tmp_path)
    r = extractor.ground(_req("C", "Proposals should contain: 9. A free pony for every adjuster "
                              "in the northern region.", _sid(doc, "13.")), doc, 90)
    assert r.quote_match_score < 90


def test_bidding_process_sections_are_skipped(tmp_path):
    doc = _doc(tmp_path)
    skip = extractor.skipped_section_ids(doc.sections, get_settings().extract_skip_titles)
    titles = {s.title for s in doc.sections if s.id in skip}
    assert titles == {"12. Evaluation Criteria", "13. Submission Instructions"}
    assert extractor.skipped_section_ids(doc.sections, "") == set()


def test_feedback_is_scoped_to_the_group():
    group = [_req("FR-01", "q", "S1"), _req("FR-02", "q", "S1")]
    fb = architect.feedback_for_group([
        "These must-priority requirements are not addressed: FR-01, INT-03, SEC-02. Add them.",
        "Risks reference SEC-09 only.",
        "Approach item 3 is a catch-all; split it.",
    ], group)
    assert fb == ["These must-priority requirements are not addressed: FR-01. Add them.",
                  "Approach item 3 is a catch-all; split it."]


def test_architect_corrects_missing_and_unknown_ids_within_the_group(tmp_path):
    reqs = [_req("FR-01", "q1", "S1"), _req("FR-02", "q2", "S1"),
            _req("FR-03", "q3", "S1", priority="should")]
    bad = {"action": "final", "approach": [{"requirement_ids": ["FR-01", "INT-99"],
           "summary": "s", "components": [], "rationale": "r"}], "assumptions": []}
    good = {"action": "final", "approach": [{"requirement_ids": ["FR-01", "FR-02", "INT-99"],
            "summary": "s", "components": [], "rationale": "r"}], "assumptions": []}
    client = FakeLLMClient({"design_approach": [bad, good]})
    ctx = _ctx(tmp_path, client)
    items, _ = architect._design_group(ctx, "Core functional capabilities", reqs, [], [0],
                                       {r.id for r in reqs})
    assert len(client.calls) == 2  # one correction turn, no more
    correction = client.calls[1]["messages"][-1]["content"]
    assert "FR-02" in correction and "INT-99" in correction
    # The id still unknown after the correction is dropped with a warning.
    assert items[0].requirement_ids == ["FR-01", "FR-02"]
    assert any("INT-99" in w for w in ctx.warnings)


def test_group_check_flags_catch_all_items():
    reqs = [_req(f"FR-{i:02d}", "q", "S1") for i in range(1, 15)]
    item = ApproachItem(requirement_ids=[r.id for r in reqs], summary="all", components=[],
                        rationale="r")
    problems = architect.check_group_answer([item], reqs, {r.id for r in reqs}, 12)
    assert any("14 ids" in p for p in problems)


def test_llm_review_never_blocks(tmp_path):
    from rfp_agent.agents import critic
    client = FakeLLMClient({"critic": [{"issues": [{
        "severity": "high", "target_node": "design_approach",
        "feedback": "The approach uses Azure.", "related_ids": []}]}]})
    issues = critic.llm_review(_ctx(tmp_path, client), [], [], [])
    assert [(i.severity, i.check) for i in issues] == [("medium", "llm_review")]
    assert issues[0].feedback.startswith("[LLM reviewer rated high]")


CONTEXT_RFP = """# RFP

## 4. Current Environment

The Company operates two data centres in Malaysia. All internal applications must use single sign-on.

## 5. Functional Requirements

Adjusters will not adopt a tool that forces them to switch screens.
"""


def test_context_sections_keep_only_stated_obligations(tmp_path):
    p = tmp_path / "rfp.md"
    p.write_text(CONTEXT_RFP)
    doc = load_document(p)
    ctx = _ctx(tmp_path, FakeLLMClient({}))
    ctx.doc = doc
    env, fr = _sid(doc, "4."), _sid(doc, "5.")
    reqs = [_req("A", "The Company operates two data centres in Malaysia.", env),
            _req("B", "All internal applications must use single sign-on.", env),
            _req("C", "Adjusters will not adopt a tool that forces them to switch screens.", fr)]
    kept = extractor.drop_context_facts(ctx, reqs)
    # context fact dropped; stated obligation kept; implied requirement elsewhere kept
    assert [r.id for r in kept] == ["B", "C"]


def test_same_quote_same_priority_merges_and_records_parts(tmp_path):
    q = "Bidders should explain how they will evaluate model quality and detect drift."
    reqs = [Requirement(id="tmp", title=t, description=t, category="non_functional",
                        priority="should", source_section="S01", source_quote=q,
                        confidence=0.9, quote_match_score=100)
            for t in ("Model quality evaluation", "Detect model drift", "Measure routing accuracy")]
    out = extractor.dedupe_and_number(_ctx(tmp_path, FakeLLMClient({})), reqs)
    assert len(out) == 1
    assert "Also covers:" in out[0].description
    assert "Detect model drift" in out[0].description or out[0].title == "Detect model drift"
