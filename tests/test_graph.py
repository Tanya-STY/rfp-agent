"""End-to-end graph run with a scripted FakeLLMClient: fully offline, runs in ~1s."""

import json
from pathlib import Path

import pytest

from rfp_agent.cli import run
from rfp_agent.schemas import SolutionSummary

from .fakes import FakeLLMClient, ids_in_prompt

MINI = str(Path(__file__).parent / "fixtures" / "mini_rfp.md")


def draft(title, quote, section, category="functional", priority="must", desc=None):
    return {"title": title, "description": desc or title, "category": category,
            "priority": priority, "section_id": section, "source_quote": quote,
            "confidence": 0.9}


UPLOAD = draft("Upload PDF documents", "The system shall allow users to upload PDF documents.", "S01")
SEARCH = draft("Full-text search", "The system shall provide full-text search across all documents.", "S01")
# Same requirement extracted twice (e.g. overlapping batches) -> must be merged by dedupe.
UPLOAD_DUP = dict(UPLOAD, confidence=0.7)
TIMELINE = draft("Pilot live by 30 June", "The pilot must go live by 30 June.", "S03", "timeline")
# Hallucinated quote: the RFP never mentions Malaysia.
RESIDENCY_BAD = draft("Data residency", "All data must remain in Malaysia.", "S02",
                      "security_compliance", desc="Data stays in the client's data centre")
RESIDENCY_GOOD = draft("Data residency", "All data must be stored in the client's own data centre.",
                       "S02", "security_compliance", desc="Data stays in the client's data centre")


def design_final(messages):
    """Architect: cover every must id the prompt lists (ids change between passes)."""
    return {"action": "final", "approach": [{
        "requirement_ids": ids_in_prompt(messages), "summary": "On-prem document portal.",
        "components": ["Upload service", "Search index"], "rationale": "Meets residency."}],
        "assumptions": [{"statement": "Client provides servers.", "rationale": "Not stated."}]}


def risks(messages):
    ids = [i for i in ("TL-01", "SEC-01") if i in messages[-1]["content"]]
    return {"risks": [{"title": "Deadline vs on-prem hosting", "description": "Tension.",
                       "category": "requirement_conflict", "likelihood": "high", "impact": "high",
                       "mitigation": "Agree interim hosting.", "related_requirement_ids": ids,
                       "source_quote": "The pilot must go live by 30 June."}],
            "open_questions": [{"question": "Is 30 June fixed?", "reason": "Tension."}]}


def scripts(extract_responses):
    return {
        "extract_requirements": extract_responses,
        "design_approach": [{"action": "search", "query": "hosting constraints"}, design_final,
                            design_final],  # pass 1: search then final; pass 2: final
        "analyze_risks": [risks],
        "critic": [{"issues": []}],
        "assemble": [{"executive_summary": "Client wants an on-prem document portal."}],
    }


@pytest.fixture
def runs_dir(tmp_path):
    return tmp_path / "runs"


def test_full_graph_with_revision(runs_dir, tmp_path):
    client = FakeLLMClient(scripts([
        {"requirements": [UPLOAD, SEARCH, UPLOAD_DUP, RESIDENCY_BAD, TIMELINE],
         "open_questions": [{"question": "Which browsers?", "reason": "Not stated."}]},
        {"requirements": [RESIDENCY_GOOD]},  # targeted re-extraction after critic feedback
    ]))
    path, tracer = run(MINI, run_id="t1", client=client, runs_dir=runs_dir,
                       cache_dir=tmp_path / "cache")
    summary = SolutionSummary.model_validate_json(Path(path).read_text())

    # dedupe merged the duplicate upload, and the grounded residency replaced the bad one
    assert [r.id for r in summary.requirements] == ["FR-01", "FR-02", "SEC-01", "TL-01"]
    sec = next(r for r in summary.requirements if r.id == "SEC-01")
    assert "client's own data centre" in sec.source_quote
    assert all(r.quote_match_score >= 90 for r in summary.requirements)

    md = summary.metadata
    assert md.revisions == 1 and md.critic_passed
    assert not md.critic_history[0].passed and md.critic_history[1].passed
    assert md.dropped_requirements == []
    assert {"extract_requirements", "design_approach", "analyze_risks", "critic",
            "executive_summary"} <= set(md.prompt_versions)

    # The revision prompt carried the critic's feedback and only the focus passage.
    revision_prompt = client.calls[[c["node"] for c in client.calls].index(
        "extract_requirements", 1)]["messages"][-1]["content"]
    assert "not verbatim" in revision_prompt and "(re-read)" in revision_prompt
    assert "FR-2 Search" not in revision_prompt

    # architect designed one item per workstream group, used its tool once, covered all ids
    assert [a.requirement_ids for a in summary.approach] == [["FR-01", "FR-02"], ["SEC-01"],
                                                             ["TL-01"]]
    assert summary.risks[0].related_requirement_ids == ["TL-01", "SEC-01"]
    # the injected sentence in S03 was quarantined at ingest and flagged for a human
    qs = [q.question for q in summary.open_questions]
    assert "Which browsers?" in qs
    assert any("addressed to automated tools" in q for q in qs)
    assert any("quarantined" in w for w in md.warnings)

    # outputs + trace
    run_dir = runs_dir / "t1"
    assert (run_dir / "summary.md").read_text().startswith("# RFP Solution Summary")
    events = [json.loads(line) for line in (run_dir / "trace.jsonl").read_text().splitlines()]
    calls = [e for e in events if e["type"] == "llm_call" and e["kind"] == "chat"]
    assert calls and all(e["prompt_version"] == md.prompt_versions[
        "executive_summary" if e["node"] == "assemble" else e["node"]] for e in calls)
    assert {e["node"] for e in calls} == {"extract_requirements", "design_approach",
                                          "analyze_risks", "critic", "assemble"}
    assert any(e["type"] == "event" and e["name"] == "tool_call" for e in events)
    spans = [e["node"] for e in events if e["type"] == "span_end"]
    assert spans.count("critic") == 2 and spans[-1] == "assemble"
    assert tracer.totals()["calls"] > 0


def test_ungrounded_requirement_dropped_when_out_of_revisions(runs_dir, tmp_path):
    client = FakeLLMClient(scripts([
        {"requirements": [UPLOAD, SEARCH, RESIDENCY_BAD, TIMELINE]},
    ]))
    path, _ = run(MINI, run_id="t2", client=client, runs_dir=runs_dir,
                  cache_dir=tmp_path / "cache", max_revisions=0)
    summary = SolutionSummary.model_validate_json(Path(path).read_text())
    assert "SEC-01" not in [r.id for r in summary.requirements]
    dropped = summary.metadata.dropped_requirements
    assert len(dropped) == 1 and dropped[0].requirement.source_quote == "All data must remain in Malaysia."
    assert not summary.metadata.critic_passed
    # references to the dropped id were pruned, and that was recorded
    assert all("SEC-01" not in a.requirement_ids for a in summary.approach)
    assert any("SEC-01" in w for w in summary.metadata.warnings)


def test_truncated_extraction_batch_is_split_and_retried(tmp_path):
    from rfp_agent.agents import extractor
    from rfp_agent.config import Settings
    from rfp_agent.context import RunContext
    from rfp_agent.ingest import load_document
    from rfp_agent.llm import OutputTruncatedError
    from rfp_agent.tracing import Tracer

    def truncate(_messages):
        raise OutputTruncatedError("cut off")

    def by_section(messages):  # answer with the requirement for whichever section is shown
        text = messages[-1]["content"]
        return {"requirements": [UPLOAD] if "[S01]" in text else [RESIDENCY_GOOD]}

    client = FakeLLMClient({"extract_requirements": [truncate, by_section]})
    ctx = RunContext(settings=Settings(), client=client, tracer=Tracer("t", tmp_path))
    ctx.doc = load_document(MINI)
    reqs, _ = extractor.extract(ctx, ctx.doc.sections[:2])
    assert [r.title for r in reqs] == ["Upload PDF documents", "Data residency"]
    assert any("splitting" in w for w in ctx.warnings)


def test_dedupe_merges_duplicates_but_keeps_distinct_obligations_sharing_a_quote(tmp_path):
    from rfp_agent.agents import extractor
    from rfp_agent.config import Settings
    from rfp_agent.context import RunContext
    from rfp_agent.schemas import Requirement
    from rfp_agent.tracing import Tracer

    def req(title, quote, priority="must"):
        return Requirement(id="tmp", title=title, description=title, category="functional",
                           priority=priority, source_section="S01", source_quote=quote,
                           confidence=0.9, quote_match_score=100)

    lang = "Bahasa is expected. Chinese would be welcome."
    reqs = [
        req("Fraud flagging", "Fraud flagging for SIU."),
        req("Fraud flagging", "FR-7 The solution shall flag fraud indicators for SIU review."),
        req("Support Bahasa Malaysia documents", lang, "should"),
        req("Handle Chinese language input", lang, "could"),
    ]
    ctx = RunContext(settings=Settings(), client=FakeLLMClient({}), tracer=Tracer("t", tmp_path))
    out = extractor.dedupe_and_number(ctx, reqs)
    assert [r.id for r in out] == ["FR-01", "FR-02", "FR-03"]
    # the longer, labelled quote survives the merge (keeps FR-7 traceable)
    assert any(r.source_quote.startswith("FR-7") for r in out)
    assert {r.priority for r in out if r.source_quote == lang} == {"should", "could"}
