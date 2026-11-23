"""Critic: deterministic checks first, then an LLM review.

Deterministic checks are cheap, exact and explainable, so they own everything that can
be verified mechanically:

* ``grounding``          every requirement's source_quote is in the RFP (quote_in_source)
* ``duplicate_ids``      requirement ids are unique
* ``numbered_coverage``  every explicitly labelled RFP requirement (e.g. "FR-7", "SEC-2"
                         at the start of a paragraph) is covered by some extracted quote
* ``must_coverage``      every must-requirement is addressed by an approach item
* ``approach_granularity`` no catch-all approach item listing > N requirement ids
* ``approach_dates``     dates in approach items are supported by the RFP (rfp_agent.dates)
* ``approach_ids`` / ``risk_ids``  references point at existing requirement ids
* ``risk_quotes``        optional risk quotes are grounded

The LLM review then looks only for judgement-level problems. Only ``high`` severity
issues fail the report (blocking); the rest are recorded for the bid team.
"""

from __future__ import annotations

import logging
import re

from ..context import RunContext
from ..dates import unsupported_dates
from ..ingest import Document
from ..retrieval import quote_in_source
from .extractor import skipped_section_ids
from ..schemas import ApproachItem, CriticIssue, CriticLLMReview, CriticReport, Requirement, Risk

log = logging.getLogger("rfp_agent")
NODE = "critic"

# A requirement label that *defines* a requirement: at the start of a paragraph,
# optionally bold, e.g. "**FR-7 Fraud indicators.**" or "SEC-1 Data residency".
_LABEL = re.compile(r"^\s*(?:[-*]\s+)?\**\s*([A-Z]{2,5}-\d{1,3})\b", re.MULTILINE)


def labelled_requirements(doc: Document) -> list[tuple[str, str, str]]:
    """(label, section_id, paragraph) for every labelled requirement paragraph."""
    out = []
    for s in doc.sections:
        for para in re.split(r"\n\s*\n", s.text):
            m = _LABEL.match(para)
            if m:
                out.append((m.group(1), s.id, para.strip()))
    return out


def deterministic_checks(doc: Document, requirements: list[Requirement],
                         approach: list[ApproachItem], risks: list[Risk],
                         threshold: float = 90.0, max_ids_per_item: int = 12,
                         skip_sections: set[str] | frozenset[str] = frozenset()
                         ) -> list[CriticIssue]:
    issues: list[CriticIssue] = []
    ids = [r.id for r in requirements]
    valid = set(ids)

    # 1. grounding
    for r in requirements:
        section = doc.section(r.source_section)
        score = quote_in_source(r.source_quote, section.text if section else doc.text).score
        if score < threshold:
            score = max(score, quote_in_source(r.source_quote, doc.text).score)
        if score < threshold:
            issues.append(CriticIssue(
                severity="high", target_node="extract_requirements", check="grounding",
                related_ids=[r.id], section_id=r.source_section,
                feedback=(f"{r.id} '{r.title}': source_quote is not verbatim in the RFP "
                          f"(match {score:.0f}/100). Copy the exact sentence from section "
                          f"{r.source_section}, or drop the requirement if it is not stated.")))

    # 2. duplicate ids
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        issues.append(CriticIssue(severity="high", target_node="extract_requirements",
                                  check="duplicate_ids", related_ids=[dup],
                                  feedback=f"Requirement id {dup} is used more than once."))

    # 3. labelled requirements in the RFP must be covered by some extracted quote
    for label, section_id, para in labelled_requirements(doc):
        if section_id in skip_sections:  # bidding-process sections are not extracted
            continue
        covered = any(quote_in_source(r.source_quote, para).ok(threshold) for r in requirements)
        if not covered:
            issues.append(CriticIssue(
                severity="high", target_node="extract_requirements", check="numbered_coverage",
                section_id=section_id, passage=para,
                feedback=f"RFP requirement {label} (section {section_id}) was not extracted."))

    # 4. must-coverage by the approach
    covered_ids = {i for a in approach for i in a.requirement_ids}
    missing = [r.id for r in requirements if r.priority == "must" and r.id not in covered_ids]
    if not approach:
        issues.append(CriticIssue(severity="high", target_node="design_approach",
                                  check="must_coverage", feedback="No approach items produced."))
    elif missing:
        issues.append(CriticIssue(
            severity="high", target_node="design_approach", check="must_coverage",
            related_ids=missing,
            feedback=("These must-priority requirements are not addressed by any approach "
                      f"item: {', '.join(missing)}. Add them to the relevant items.")))

    # 4b. granularity: a catch-all item that lists everything is a way of gaming 4.
    for n, a in enumerate(approach, 1):
        if len(a.requirement_ids) > max_ids_per_item:
            issues.append(CriticIssue(
                severity="high", target_node="design_approach", check="approach_granularity",
                feedback=(f"Approach item {n} ('{a.summary[:60]}') lists {len(a.requirement_ids)} "
                          f"requirement ids; split it into focused workstreams of at most "
                          f"{max_ids_per_item} ids each.")))

    # 4c. dates in the approach must be supported by the RFP (phase 4: an approach item
    #     invented "pilot go-live on October 15, 2024"; approach items have no quote to check)
    for n, a in enumerate(approach, 1):
        bad = unsupported_dates(f"{a.summary} {a.rationale}", doc.text)
        if bad:
            issues.append(CriticIssue(
                severity="high", target_node="design_approach", check="approach_dates",
                related_ids=a.requirement_ids,
                feedback=(f"Approach item {n} ('{a.summary[:60]}') uses dates the RFP does not "
                          f"state: {', '.join(bad)}. Use the RFP's own dates for "
                          f"{', '.join(a.requirement_ids)}, or describe timing without a date.")))

    # 5. referential integrity
    bad = sorted({i for a in approach for i in a.requirement_ids if i not in valid})
    if bad:
        issues.append(CriticIssue(
            severity="high", target_node="design_approach", check="approach_ids", related_ids=bad,
            feedback=f"Approach references unknown requirement ids {', '.join(bad)}. "
                     "Use only ids from the requirement list."))
    bad = sorted({i for k in risks for i in k.related_requirement_ids if i not in valid})
    if bad:
        issues.append(CriticIssue(
            severity="high", target_node="analyze_risks", check="risk_ids", related_ids=bad,
            feedback=f"Risks reference unknown requirement ids {', '.join(bad)}. "
                     "Use only ids from the requirement list."))
    if not risks:
        issues.append(CriticIssue(severity="high", target_node="analyze_risks",
                                  check="risk_ids", feedback="No risks produced."))

    # 6. optional risk quotes must be grounded if present
    for k in risks:
        if k.source_quote and not quote_in_source(k.source_quote, doc.text).ok(threshold):
            issues.append(CriticIssue(
                severity="medium", target_node="analyze_risks", check="risk_quotes",
                related_ids=[k.id],
                feedback=f"{k.id}: source_quote is not verbatim in the RFP; copy it exactly "
                         "or set it to null."))
    return issues


def llm_review(ctx: RunContext, requirements, approach, risks) -> list[CriticIssue]:
    prompt = ctx.prompt(NODE)
    out = ctx.client.chat_structured(
        prompt.render(requirements=requirements, approach=approach, risks=risks),
        CriticLLMReview, node_name=NODE, temperature=ctx.settings.temperature_critic,
        prompt_version=prompt.version)
    # The LLM review is advisory: it never blocks. In live run 6 it raised "high" issues
    # that were false (claimed the approach used Azure / a REST API when it explicitly
    # avoided both) and spent both revisions on them (failure log F10, F18). Its issues
    # are kept for the bid team, capped at medium.
    issues = []
    for i in out.issues[:5]:
        d = i.model_dump()
        if d["severity"] == "high":
            d["severity"] = "medium"
            d["feedback"] = "[LLM reviewer rated high] " + d["feedback"]
        issues.append(CriticIssue(**d, check="llm_review"))
    return issues


def review(ctx: RunContext, requirements, approach, risks, revision: int) -> CriticReport:
    assert ctx.doc is not None
    issues = deterministic_checks(ctx.doc, requirements, approach, risks,
                                  ctx.settings.quote_match_threshold,
                                  ctx.settings.max_ids_per_approach_item,
                                  skipped_section_ids(ctx.doc.sections,
                                                      ctx.settings.extract_skip_titles))
    n_det = len(issues)
    issues += llm_review(ctx, requirements, approach, risks)
    report = CriticReport(passed=not any(i.severity == "high" for i in issues),
                          issues=issues, revision=revision)
    log.info("  critic: %d deterministic + %d llm issues, %d blocking -> %s",
             n_det, len(issues) - n_det, len(report.blocking()),
             "PASS" if report.passed else "FAIL")
    ctx.tracer.event("critic_report", passed=report.passed, revision=revision,
                     issues=[i.model_dump(exclude={"passage"}) for i in issues])
    return report
