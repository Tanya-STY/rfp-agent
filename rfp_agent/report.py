"""Final assembly: enforce invariants, write the executive summary, render outputs."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from .context import RunContext
from .retrieval import normalize_for_match, quote_in_source
from .schemas import (
    ApproachItem,
    DroppedRequirement,
    ExecutiveSummaryOutput,
    OpenQuestion,
    Requirement,
    Risk,
    SolutionSummary,
)

log = logging.getLogger("rfp_agent")
NODE = "assemble"


def drop_ungrounded(ctx: RunContext, requirements: list[Requirement]
                    ) -> tuple[list[Requirement], list[DroppedRequirement]]:
    """Requirements whose quote still fails verification are removed, never silently kept."""
    assert ctx.doc is not None
    thr = ctx.settings.quote_match_threshold
    kept, dropped = [], []
    for r in requirements:
        score = quote_in_source(r.source_quote, ctx.doc.text).score
        if score >= thr:
            kept.append(r.model_copy(update={"quote_match_score": score}))
        else:
            dropped.append(DroppedRequirement(
                requirement=r.model_copy(update={"quote_match_score": score}),
                reason=f"source_quote not found in RFP after revisions (match {score:.0f}/100)"))
    return kept, dropped


def prune_references(approach: list[ApproachItem], risks: list[Risk], valid: set[str],
                     warnings: list[str]) -> tuple[list[ApproachItem], list[Risk]]:
    """Strip references to ids that do not exist (after drops / failed revisions)."""
    def clean(ids: list[str], owner: str) -> list[str]:
        bad = [i for i in ids if i not in valid]
        if bad:
            warnings.append(f"{owner}: removed references to unknown ids {bad}")
        return [i for i in ids if i in valid]

    approach = [a.model_copy(update={"requirement_ids": clean(a.requirement_ids, "approach")})
                for a in approach]
    risks = [k.model_copy(update={"related_requirement_ids":
                                  clean(k.related_requirement_ids, k.id)}) for k in risks]
    return approach, risks


def dedupe_questions(questions: list[OpenQuestion]) -> list[OpenQuestion]:
    seen, out = set(), []
    for q in questions:
        key = normalize_for_match(q.question)
        if key and key not in seen:
            seen.add(key)
            out.append(q)
    return out


def executive_summary(ctx: RunContext, requirements, approach, risks) -> str:
    prompt = ctx.prompt("executive_summary")
    title = ctx.doc.sections[0].title if ctx.doc and ctx.doc.sections else "RFP"
    must = [r for r in requirements if r.priority == "must"][:25]
    top_risks = sorted(risks, key=lambda k: ({"high": 0, "medium": 1, "low": 2}[k.impact],
                                             {"high": 0, "medium": 1, "low": 2}[k.likelihood]))[:5]
    out = ctx.client.chat_structured(
        prompt.render(title=title, requirements=must, approach=approach, risks=top_risks),
        ExecutiveSummaryOutput, node_name=NODE, temperature=ctx.settings.temperature_design,
        prompt_version=prompt.version)
    return out.executive_summary


def write_outputs(summary: SolutionSummary, run_dir: Path) -> tuple[Path, Path]:
    run_dir.mkdir(parents=True, exist_ok=True)
    j = run_dir / "summary.json"
    j.write_text(summary.model_dump_json(indent=2), encoding="utf-8")
    m = run_dir / "summary.md"
    m.write_text(render_markdown(summary), encoding="utf-8")
    return j, m


def _cell(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ")


def render_markdown(s: SolutionSummary) -> str:
    md = s.metadata
    lines = [
        f"# RFP Solution Summary - {Path(md.input_file).name}", "",
        f"_Run `{md.run_id}` - model `{md.model}` - critic "
        f"{'passed' if md.critic_passed else 'did NOT pass'} after {md.revisions} revision(s)_", "",
        "## Executive summary", "", s.executive_summary, "",
        f"## Requirements ({len(s.requirements)})", "",
        "| ID | Priority | Title | Description | Source | Quote |",
        "|---|---|---|---|---|---|",
    ]
    for r in s.requirements:
        lines.append(f"| {r.id} | {r.priority} | {_cell(r.title)} | {_cell(r.description)} | "
                     f"{r.source_section} | \"{_cell(r.source_quote)}\" |")
    lines += ["", f"## Solution approach ({len(s.approach)})", ""]
    for i, a in enumerate(s.approach, 1):
        lines += [f"### {i}. {a.summary}", "",
                  f"- **Addresses:** {', '.join(a.requirement_ids) or '-'}",
                  f"- **Components:** {', '.join(a.components) or '-'}",
                  f"- **Rationale:** {a.rationale}", ""]
    lines += [f"## Risks ({len(s.risks)})", "",
              "| ID | Category | Title | L | I | Mitigation | Related |",
              "|---|---|---|---|---|---|---|"]
    for k in s.risks:
        lines.append(f"| {k.id} | {k.category} | **{_cell(k.title)}** - {_cell(k.description)} | "
                     f"{k.likelihood} | {k.impact} | {_cell(k.mitigation)} | "
                     f"{', '.join(k.related_requirement_ids)} |")
    if s.assumptions:
        lines += ["", "## Assumptions", ""]
        lines += [f"- {a.statement}" + (f" _({a.rationale})_" if a.rationale else "")
                  for a in s.assumptions]
    if s.open_questions:
        lines += ["", "## Open questions for the client", ""]
        lines += [f"- {q.question}" + (f" _({q.reason})_" if q.reason else "")
                  for q in s.open_questions]
    if md.dropped_requirements:
        lines += ["", "## Dropped requirements (failed grounding)", ""]
        lines += [f"- {d.requirement.title}: \"{d.requirement.source_quote}\" - {d.reason}"
                  for d in md.dropped_requirements]
    if md.critic_history:
        lines += ["", "## Critic history", ""]
        for rep in md.critic_history:
            lines.append(f"- Pass {rep.revision}: {'PASS' if rep.passed else 'FAIL'} - "
                         f"{len(rep.issues)} issue(s), {len(rep.blocking())} blocking")
            for i in rep.issues:
                lines.append(f"  - [{i.severity}] {i.check} -> {i.target_node}: {_cell(i.feedback)}")
    if md.warnings:
        lines += ["", "## Warnings", ""] + [f"- {w}" for w in md.warnings]
    u = md.usage
    lines += ["", "## Run metadata", "",
              f"- Prompt versions: {', '.join(f'{k}@{v}' for k, v in md.prompt_versions.items())}",
              f"- LLM calls: {int(u.get('calls', 0))}, prompt tokens: {int(u.get('prompt_tokens', 0))}, "
              f"completion tokens: {int(u.get('completion_tokens', 0))}, "
              f"model latency: {u.get('latency_ms', 0) / 1000:.1f}s, "
              f"cost: ${u.get('cost_usd', 0):.4f}",
              f"- Wall time: {(md.finished_at - md.started_at).total_seconds():.1f}s"
              if md.finished_at else "", ""]
    return "\n".join(lines)


def now() -> datetime:
    return datetime.now(timezone.utc)
