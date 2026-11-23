from pathlib import Path

from rfp_agent.agents.critic import deterministic_checks, labelled_requirements
from rfp_agent.ingest import load_document
from rfp_agent.schemas import ApproachItem, Requirement, Risk

DOC = load_document(Path(__file__).parent / "fixtures" / "mini_rfp.md")


def req(id, quote, priority="must", section="S01", category="functional"):
    return Requirement(id=id, title=id, description=id, category=category, priority=priority,
                       source_section=section, source_quote=quote, confidence=0.9)


GOOD = [
    req("FR-01", "The system shall allow users to upload PDF documents."),
    req("FR-02", "The system shall provide full-text search across all documents."),
    req("SEC-01", "All data must be stored in the client's own data centre.", section="S02",
        category="security_compliance"),
    req("TL-01", "The pilot must go live by 30 June.", section="S03", category="timeline"),
]
APPROACH = [ApproachItem(requirement_ids=["FR-01", "FR-02", "SEC-01", "TL-01"], summary="s",
                         rationale="r")]
RISKS = [Risk(id="R-01", title="t", description="d", category="requirement_conflict",
              likelihood="high", impact="high", mitigation="m",
              related_requirement_ids=["TL-01", "SEC-01"])]


def checks(issues):
    return sorted({i.check for i in issues})


def test_clean_draft_has_no_issues():
    assert deterministic_checks(DOC, GOOD, APPROACH, RISKS) == []


def test_labels_found():
    assert [label for label, _, _ in labelled_requirements(DOC)] == ["FR-1", "FR-2", "SEC-1"]


def test_ungrounded_quote_is_blocking_and_targets_extractor():
    bad = GOOD[:2] + [req("SEC-01", "All data must remain in Malaysia.", section="S02",
                          category="security_compliance")] + GOOD[3:]
    issues = deterministic_checks(DOC, bad, APPROACH, RISKS)
    grounding = [i for i in issues if i.check == "grounding"]
    assert len(grounding) == 1 and grounding[0].severity == "high"
    assert grounding[0].target_node == "extract_requirements"
    assert grounding[0].related_ids == ["SEC-01"]
    # SEC-1 paragraph is now uncovered too, with the passage attached for re-reading.
    cov = [i for i in issues if i.check == "numbered_coverage"]
    assert len(cov) == 1 and "SEC-1" in cov[0].feedback and cov[0].passage


def test_duplicate_ids():
    issues = deterministic_checks(DOC, GOOD + [GOOD[0]], APPROACH, RISKS)
    assert "duplicate_ids" in checks(issues)


def test_must_requirement_not_in_approach():
    approach = [ApproachItem(requirement_ids=["FR-01"], summary="s", rationale="r")]
    issues = deterministic_checks(DOC, GOOD, approach, RISKS)
    must = [i for i in issues if i.check == "must_coverage"][0]
    assert must.target_node == "design_approach"
    assert set(must.related_ids) == {"FR-02", "SEC-01", "TL-01"}


def test_invalid_ids_in_approach_and_risks():
    approach = APPROACH + [ApproachItem(requirement_ids=["FR-99"], summary="s", rationale="r")]
    risks = [RISKS[0].model_copy(update={"related_requirement_ids": ["NFR-07"]})]
    issues = deterministic_checks(DOC, GOOD, approach, risks)
    by_check = {i.check: i for i in issues}
    assert by_check["approach_ids"].related_ids == ["FR-99"]
    assert by_check["risk_ids"].target_node == "analyze_risks"


def test_ungrounded_risk_quote_is_non_blocking():
    risks = [RISKS[0].model_copy(update={"source_quote": "Budget is unlimited."})]
    issues = deterministic_checks(DOC, GOOD, APPROACH, risks)
    assert [(i.check, i.severity) for i in issues] == [("risk_quotes", "medium")]


def test_priority_from_modal_verbs():
    from rfp_agent.agents.extractor import priority_from_quote as p
    assert p("Classification should complete within 30 seconds.") == "should"
    assert p("The solution shall not write to the PAS.") == "must"
    assert p("If Chinese could be handled, that would be welcome.") == "could"
    assert p("Claims are managed in ClaimsNet.") is None  # no modal: keep model's call
    assert p("X shall be done and Y should be done.") is None  # mixed: ambiguous
    # "may ... only" is a restriction, not an option - "may" is deliberately not mapped
    assert p("The solution may hold working copies only while processing.") is None


def test_catch_all_approach_item_is_rejected():
    big = [ApproachItem(requirement_ids=["FR-01", "FR-02", "SEC-01", "TL-01"], summary="all",
                        rationale="r")]
    issues = deterministic_checks(DOC, GOOD, big, RISKS, max_ids_per_item=3)
    assert [i.check for i in issues] == ["approach_granularity"]
