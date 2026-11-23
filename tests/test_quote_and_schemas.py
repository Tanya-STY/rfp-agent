import pytest
from pydantic import ValidationError

from rfp_agent.retrieval import normalize_for_match, quote_in_source, snap_quote
from rfp_agent.schemas import ExtractionOutput, Requirement, SolutionSummary

SOURCE = (
    "**FR-7 Fraud indicators.** The solution shall identify potential fraud indicators "
    "(for example, inconsistent dates) and refer flagged claims to SIU with an explanation. "
    "The solution must never automatically decline or close a claim."
)


# ---------------------------------------------------------------- quote_in_source
def test_exact_quote():
    m = quote_in_source("The solution must never automatically decline or close a claim.", SOURCE)
    assert m.exact and m.score == 100


def test_case_whitespace_punctuation_normalised():
    m = quote_in_source("the solution MUST never  automatically decline, or close a claim", SOURCE)
    assert m.exact and m.ok()


def test_smart_quotes_and_markdown_ignored():
    assert normalize_for_match("**FR-7** “Fraud”") == normalize_for_match('FR-7 "Fraud"')


def test_near_miss_is_fuzzy_match():
    m = quote_in_source("The solution must never automatically decline or close claims", SOURCE)
    assert not m.exact and m.score >= 90


def test_paraphrase_fails():
    m = quote_in_source("Claims may not be rejected by the AI without a human.", SOURCE)
    assert not m.ok()


def test_short_generic_quote_is_not_trusted():
    assert not quote_in_source("the solution shall", SOURCE).ok()


def test_snap_repairs_near_miss_to_exact_source_span():
    quote, m = snap_quote("The solution must never automatically decline or close claims", SOURCE)
    assert quote in SOURCE and quote.startswith("The solution")  # whole words, not "he solution"


def test_snap_leaves_hallucination_alone():
    q = "All data must remain in Malaysia."
    assert snap_quote(q, SOURCE)[0] == q


# ------------------------------------------------------------------------ schemas
def _req(**kw):
    base = dict(id="FR-01", title="t", description="d", category="functional", priority="must",
                source_section="S01", source_quote="q", confidence=0.9)
    return Requirement(**{**base, **kw})


def test_requirement_valid():
    assert _req().priority == "must"


@pytest.mark.parametrize("field,value", [("category", "legal"), ("priority", "high"),
                                         ("confidence", 1.5)])
def test_requirement_rejects_bad_values(field, value):
    with pytest.raises(ValidationError):
        _req(**{field: value})


def test_llm_schema_is_json_schema_for_ollama_format():
    schema = ExtractionOutput.model_json_schema()
    assert schema["type"] == "object" and "requirements" in schema["properties"]


def test_extraction_output_parses_json():
    raw = ('{"requirements": [{"title": "x", "description": "y", "category": "timeline", '
           '"priority": "could", "section_id": "S01", "source_quote": "q", "confidence": 0.5}]}')
    out = ExtractionOutput.model_validate_json(raw)
    assert out.requirements[0].category == "timeline" and out.open_questions == []


def test_solution_summary_roundtrip():
    from datetime import datetime, timezone

    from rfp_agent.schemas import RunMetadata
    s = SolutionSummary(executive_summary="e", requirements=[_req()], approach=[], risks=[],
                        metadata=RunMetadata(run_id="r", input_file="f", model="m",
                                             embed_model="e", started_at=datetime.now(timezone.utc)))
    assert SolutionSummary.model_validate_json(s.model_dump_json()) == s
