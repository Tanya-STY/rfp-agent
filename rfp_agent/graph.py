"""LangGraph workflow.

    ingest -> extract_requirements -> design_approach -> analyze_risks -> critic
                     ^                       ^                 ^             |
                     +-----------------------+-----------------+-------------+
                               (critic fails & revisions left)               |
                                                                             v
                                                                         assemble

Routing uses a ``pending`` list: on the first pass all three agents are pending; when
the critic fails, only the agents that own a *blocking* issue are re-queued (plus
everything downstream of extraction if extraction is re-run, because requirement ids
change). After each agent, ``_next`` jumps to the next pending agent or to the critic.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from .agents import architect, critic, extractor, risk_analyst
from .context import RunContext
from .guard import quarantine
from .ingest import Section, chunk_for_retrieval, load_document
from .report import dedupe_questions, drop_ungrounded, executive_summary, now, prune_references, write_outputs
from .retrieval import VectorIndex
from .schemas import (
    ApproachItem,
    Assumption,
    CriticIssue,
    CriticReport,
    OpenQuestion,
    Requirement,
    Risk,
    RunMetadata,
    SolutionSummary,
)
from .tracing import span

log = logging.getLogger("rfp_agent")

EXTRACT, DESIGN, RISKS = "extract_requirements", "design_approach", "analyze_risks"
PIPELINE = [EXTRACT, DESIGN, RISKS]
MAX_FOCUS_PASSAGES = 6


class GraphState(TypedDict, total=False):
    input_path: str
    started_at: datetime
    requirements: list[Requirement]
    approach: list[ApproachItem]
    assumptions: list[Assumption]
    risks: list[Risk]
    questions: dict[str, list[OpenQuestion]]  # per node, replaced when the node re-runs
    pending: list[str]
    feedback: dict[str, list[str]]
    extract_focus: list[dict[str, str]]  # passages to re-read on an extraction revision
    revision_count: int
    critic_reports: list[CriticReport]
    summary_path: str


def build_graph(ctx: RunContext):
    s = ctx.settings

    # ---------------------------------------------------------------------------- nodes
    def ingest(state: GraphState) -> dict[str, Any]:
        with span("ingest"):
            doc = load_document(state["input_path"], s.max_section_chars, s.chunk_overlap_chars)
            doc, removed = quarantine(doc)
            injected: list[OpenQuestion] = []
            for q in removed:
                ctx.warn(f"quarantined text addressed to automated tools in {q.section_id}: "
                         f"{q.text[:160]!r}")
                injected.append(OpenQuestion(
                    question=f"Section {q.section_id} contains text addressed to automated "
                             "tools; it was removed before analysis. Was it placed deliberately?",
                    reason=f"Possible prompt injection: {q.text[:200]}", raised_by="ingest"))
            ctx.tracer.event("quarantine", count=len(removed),
                             sections=[q.section_id for q in removed])
            ctx.doc = doc
            chunks = chunk_for_retrieval(doc.sections, s.retrieval_chunk_chars)
            ctx.index = VectorIndex.build(chunks, ctx.client, s.cache_dir, doc.sha, s.embed_model)
            log.info("  %d sections, %d retrieval chunks, %d chars", len(doc.sections),
                     len(chunks), len(doc.text))
            ctx.tracer.event("ingest", sections=len(doc.sections), chunks=len(chunks),
                             chars=len(doc.text), path=doc.path)
        return {"pending": list(PIPELINE), "revision_count": 0, "feedback": {},
                "questions": {"ingest": injected} if injected else {}, "critic_reports": [], "requirements": [], "approach": [],
                "assumptions": [], "risks": [], "extract_focus": []}

    def extract_requirements(state: GraphState) -> dict[str, Any]:
        with span(EXTRACT, revision=state["revision_count"]):
            assert ctx.doc is not None
            feedback = state["feedback"].get(EXTRACT, [])
            questions = dict(state["questions"])
            if state["revision_count"] == 0:
                skip = extractor.skipped_section_ids(ctx.doc.sections, s.extract_skip_titles)
                if skip:
                    log.info("  skipping bidding-process sections: %s", ", ".join(sorted(skip)))
                    ctx.tracer.event("extract_skip", sections=sorted(skip))
                new, qs = extractor.extract(ctx, [x for x in ctx.doc.sections if x.id not in skip])
                combined = new
                questions[EXTRACT] = qs
            else:
                # Targeted re-extraction: only re-read the passages the critic pointed at,
                # then merge with what we already have (dedupe keeps grounded versions).
                focus = [Section(id=f["section_id"], title=f["title"] + " (re-read)", level=2,
                                 text=f["text"]) for f in state["extract_focus"]]
                new, qs = extractor.extract(ctx, focus, feedback)
                # Requirements the critic found ungrounded are REPLACED by the re-read, not
                # kept alongside it - otherwise the same bad quotes fail every pass (F14).
                last = state["critic_reports"][-1] if state["critic_reports"] else None
                bad = {i for x in (last.issues if last else []) if x.check == "grounding"
                       for i in x.related_ids}
                combined = [r for r in state["requirements"] if r.id not in bad] + new
                questions[EXTRACT] = questions.get(EXTRACT, []) + qs
            reqs = extractor.dedupe_and_number(ctx, combined)
        pending = [n for n in state["pending"] if n != EXTRACT]
        if state["revision_count"] > 0:  # ids changed -> downstream must re-run
            pending = sorted(set(pending) | {DESIGN, RISKS}, key=PIPELINE.index)
        return {"requirements": reqs, "questions": questions, "pending": pending}

    def design_approach(state: GraphState) -> dict[str, Any]:
        with span(DESIGN, revision=state["revision_count"]):
            approach, assumptions = architect.design(ctx, state["requirements"],
                                                     state["feedback"].get(DESIGN, []))
        return {"approach": approach, "assumptions": assumptions,
                "pending": [n for n in state["pending"] if n != DESIGN]}

    def analyze_risks(state: GraphState) -> dict[str, Any]:
        with span(RISKS, revision=state["revision_count"]):
            risks, qs = risk_analyst.analyze(ctx, state["requirements"], state["approach"],
                                             state["feedback"].get(RISKS, []))
        questions = {**state["questions"], RISKS: qs}
        return {"risks": risks, "questions": questions,
                "pending": [n for n in state["pending"] if n != RISKS]}

    def critic_node(state: GraphState) -> dict[str, Any]:
        rev = state["revision_count"]
        with span("critic", revision=rev):
            report = critic.review(ctx, state["requirements"], state["approach"],
                                   state["risks"], revision=rev)
            reports = state["critic_reports"] + [report]
            if report.passed or rev >= s.max_revisions:
                if not report.passed:
                    ctx.warn(f"critic still failing after {rev} revision(s); assembling anyway")
                return {"critic_reports": reports, "pending": []}
            targets = sorted({i.target_node for i in report.blocking()}, key=PIPELINE.index)
            feedback = {n: [i.feedback for i in report.issues if i.target_node == n]
                        for n in targets}
            focus = _focus_passages(ctx, report.issues, state["requirements"]) \
                if EXTRACT in targets else []
            ctx.tracer.event("route", revision=rev + 1, targets=targets,
                             focus_sections=[f["section_id"] for f in focus])
            log.info("  routing revision %d to: %s", rev + 1, ", ".join(targets))
        return {"critic_reports": reports, "pending": targets, "feedback": feedback,
                "extract_focus": focus, "revision_count": rev + 1}

    def assemble(state: GraphState) -> dict[str, Any]:
        with span("assemble"):
            assert ctx.doc is not None
            reqs, dropped = drop_ungrounded(ctx, state["requirements"])
            for d in dropped:
                ctx.warn(f"dropped ungrounded requirement {d.requirement.id} "
                         f"'{d.requirement.title}'")
            warnings: list[str] = []
            approach, risks = prune_references(state["approach"], state["risks"],
                                               {r.id for r in reqs}, warnings)
            for w in warnings:
                ctx.warn(w)
            questions = dedupe_questions([q for qs in state["questions"].values() for q in qs])
            summary_text = executive_summary(ctx, reqs, approach, risks)
            reports = state["critic_reports"]
            meta = RunMetadata(
                run_id=ctx.tracer.run_id, input_file=ctx.doc.path, model=ctx.client.model,
                embed_model=s.embed_model, prompt_versions=dict(ctx.prompt_versions),
                started_at=state["started_at"], revisions=state["revision_count"],
                critic_passed=bool(reports and reports[-1].passed), critic_history=reports,
                dropped_requirements=dropped)
            summary = SolutionSummary(
                executive_summary=summary_text, requirements=reqs, approach=approach,
                risks=risks, assumptions=state["assumptions"], open_questions=questions,
                metadata=meta)
        # Finalise metadata after the assemble span closes so usage includes everything.
        summary.metadata.warnings = list(ctx.warnings)
        summary.metadata.usage = ctx.tracer.totals()
        summary.metadata.finished_at = now()
        json_path, _ = write_outputs(summary, ctx.tracer.run_dir)
        return {"summary_path": str(json_path)}

    # -------------------------------------------------------------------------- routing
    def _next(state: GraphState) -> str:
        return next((n for n in PIPELINE if n in state["pending"]), "critic")

    def _after_critic(state: GraphState) -> str:
        return next((n for n in PIPELINE if n in state["pending"]), "assemble")

    g = StateGraph(GraphState)
    g.add_node("ingest", ingest)
    g.add_node(EXTRACT, extract_requirements)
    g.add_node(DESIGN, design_approach)
    g.add_node(RISKS, analyze_risks)
    g.add_node("critic", critic_node)
    g.add_node("assemble", assemble)
    g.add_edge(START, "ingest")
    g.add_edge("ingest", EXTRACT)
    for n in PIPELINE:
        g.add_conditional_edges(n, _next, [*PIPELINE, "critic"])
    g.add_conditional_edges("critic", _after_critic, [*PIPELINE, "assemble"])
    g.add_edge("assemble", END)
    return g.compile()


def _focus_passages(ctx: RunContext, issues: list[CriticIssue], reqs: list[Requirement]
                    ) -> list[dict[str, str]]:
    """Pick small passages for targeted re-extraction (bounded to MAX_FOCUS_PASSAGES)."""
    assert ctx.doc is not None
    by_id = {r.id: r for r in reqs}
    out: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(section_id: str, title: str, text: str) -> None:
        key = text[:120]
        if key not in seen and len(out) < MAX_FOCUS_PASSAGES:
            seen.add(key)
            out.append({"section_id": section_id, "title": title, "text": text})

    for issue in issues:
        if issue.target_node != EXTRACT or issue.severity != "high":
            continue
        if issue.passage and issue.section_id:  # numbered requirement we know is missing
            sec = ctx.doc.section(issue.section_id)
            add(issue.section_id, sec.title if sec else "", issue.passage)
            continue
        # Otherwise find the best chunk: for a requirement, prefer chunks in its section.
        req = by_id.get(issue.related_ids[0]) if issue.related_ids else None
        query = f"{req.title}. {req.description}" if req else issue.feedback
        hits = ctx.search(query, k=8, node=EXTRACT)
        if req:
            in_section = [c for c, _ in hits if c.section_id == req.source_section]
            chunk = in_section[0] if in_section else hits[0][0]
        else:
            chunk = hits[0][0]
        add(chunk.section_id, chunk.section_title, chunk.text)
    return out


def initial_state(input_path: str) -> GraphState:
    return {"input_path": input_path, "started_at": now()}
