"""Risk-analyst agent.

Context is gathered by code, not by the model: a fixed set of risk-oriented queries
(timeline, hosting/residency, budget, legacy integration, ...) is run against the vector
index, hits are de-duplicated and capped at ``risk_context_chars``. The queries are
generic so they work for any RFP, and the cap keeps the prompt inside a small context.
"""

from __future__ import annotations

import logging
import re

from ..context import RunContext
from ..llm import StructuredOutputError
from ..ingest import Chunk
from ..retrieval import normalize_for_match
from ..schemas import ApproachItem, OpenQuestion, Requirement, Risk, RiskDraft, RiskOutput
from .architect import normalize_ids

log = logging.getLogger("rfp_agent")
NODE = "analyze_risks"

RISK_QUERIES = [
    "fixed deadline go-live date milestones timeline",
    "data residency on-premise hosting cloud restrictions",
    "hardware infrastructure procurement lead time",
    "budget envelope pricing payment terms",
    "legacy system integration constraints existing interfaces",
    "data retention deletion audit requirements",
    "performance targets real time availability",
    "expected but not required optional nice to have",
]


def gather_context(ctx: RunContext, k: int = 3) -> list[Chunk]:
    """Top hit of EVERY risk query first, then the best remaining hits by score.

    Ranking all hits by score alone let a few topics (timeline, budget, integration) fill
    the character budget, so e.g. the performance passage and the 30-day deletion rule
    never reached the analyst (failure log F17).
    """
    best: dict[str, tuple[Chunk, float]] = {}
    firsts: list[Chunk] = []
    assert ctx.index is not None
    for hits in ctx.index.search_many(RISK_QUERIES, ctx.client, k, node_name=NODE):
        if hits:
            firsts.append(hits[0][0])
        for chunk, score in hits:
            if chunk.id not in best or score > best[chunk.id][1]:
                best[chunk.id] = (chunk, score)
    ranked = firsts + [c for c, _ in sorted(best.values(), key=lambda cs: -cs[1])]
    picked: list[Chunk] = []
    seen: set[str] = set()
    used = 0
    for chunk in ranked:
        if chunk.id in seen:
            continue
        seen.add(chunk.id)
        if used + len(chunk.text) > ctx.settings.risk_context_chars:
            continue
        picked.append(chunk)
        used += len(chunk.text)
    # Present passages in document order - easier for the model to reason about.
    return sorted(picked, key=lambda c: c.id)


# ------------------------------------------------------------------ conflict candidates
#
# Phase 2 found the planted contradictions in some runs and not others (risk-step
# variance). A 7B model reliably *judges* a pair it is shown, but does not reliably *find*
# the pair among ~80 requirements. So code proposes candidate pairs from generic RFP risk
# patterns - the checklist a human bid analyst runs - and the model decides whether each
# is a real risk. Patterns are about classes of clash, never about a particular RFP.

_DATE = re.compile(r"\b(\d{1,2}(st|nd|rd|th)? (jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
                   r"[a-z]*|(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* \d{4})\b",
                   re.I)
_LEAD_TIME = re.compile(r"\b(\d+|one|two|three|four|six|eight|ten|twelve|sixteen|twenty)"
                        r"( to \d+)?[- ](weeks?|months?)\b", re.I)
_LEAD_CAUSE = re.compile(r"procure|purchase|hardware|install|consult|union|approv|board|"
                         r"accredit|certif|tender", re.I)
_ON_PREM = re.compile(r"(on[- ]prem\w*|own servers|own .{0,20}data cent\w*|in-house)"
                      r".{0,60}(host|stor|process|deploy|server|data cent)|(host|stor|process|"
                      r"deploy)\w* .{0,60}(on[- ]prem|own servers|own .{0,20}data cent)", re.I)
_SUPPLIER_HOSTED = re.compile(r"software[- ]as[- ]a[- ]service|\bsaas\b|supplier[- ]hosted|"
                              r"hosted (and operated )?by the supplier|fully managed", re.I)
_DELETE = re.compile(r"\bdelet|\bpurg|\b(not|never) be (stored|kept|retained)|shall not be "
                     r"stored|must not (store|retain|keep)", re.I)
_RETAIN = re.compile(r"\bretain|\bretention|\bkept for|\barchiv|public record|"
                     r"considerably longer", re.I)
_LABEL = re.compile(r"\b[A-Z]{1,5}-?\d{1,3}\b")
_MONEY = re.compile(r"(\$|£|€|\b(usd|gbp|eur|aud|myr|rm)\b)\s?\d|\d[\d,.]*\s?(million|m\b|k\b)"
                    r"|\bbudget (of|envelope|is|ceiling)", re.I)
_VAGUE = re.compile(r"\b(real[- ]time|quickly|promptly|timely|as soon as possible|fast|"
                    r"user[- ]friendly|intuitive|seamless|responsive)\b", re.I)


def _text(r: Requirement) -> str:
    return f"{r.title}. {r.description} {r.source_quote}"


def _ids(reqs: list[Requirement], n: int = 3) -> str:
    return "; ".join(f"{r.id} \"{r.title}\"" for r in reqs[:n])


def conflict_candidates(requirements: list[Requirement], doc=None) -> list[str]:
    """Candidate tensions and ambiguities for the analyst to confirm or reject."""
    from .extractor import sentences

    out: list[str] = []
    rank = {"must": 0, "should": 1, "could": 2}
    dated = sorted((r for r in requirements if _DATE.search(_text(r))),
                   key=lambda r: (r.category != "timeline", rank[r.priority]))
    hosting = [r for r in requirements if _ON_PREM.search(_text(r))]
    lead_reqs = [r for r in requirements
                 if _LEAD_TIME.search(r.source_quote) and _LEAD_CAUSE.search(r.source_quote)]
    lead_text = []
    if doc is not None:
        for s in doc.sections:
            for sent in sentences(s.text):
                if _LEAD_TIME.search(sent) and _LEAD_CAUSE.search(sent):
                    # Name the requirements extracted from that section, so the model can
                    # cite an id rather than only the sentence (water run: the union
                    # clash was found but cited an unrelated id).
                    para = next((x for x in s.text.split("\n\n") if sent.strip() in x), sent)
                    para_n = normalize_for_match(para)
                    near = [r for r in requirements if r not in lead_reqs and r.source_quote
                            and normalize_for_match(r.source_quote) in para_n]
                    ids = f" (same paragraph as: {_ids(near)})" if near else ""
                    lead_text.append(f"[{s.id}] \"{sent.strip()[:300]}\"{ids}")
    if dated and (lead_reqs or lead_text or hosting):
        parts = [f"fixed dates: {_ids(dated)}"]
        if hosting:
            parts.append(f"hosting constraints that force new hardware or facilities: "
                         f"{_ids(hosting)}")
        if lead_text:
            parts.append("lead times stated in the RFP: " + " ".join(lead_text[:3]))
        if lead_reqs:
            parts.append(f"lead-time requirements: {_ids(lead_reqs)}")
        cite = ("cite the date requirement AND the hosting constraint that causes the lead "
                "time" if hosting else "cite the date requirement and the requirement the lead time comes from")
        out.append("Deadline vs lead time. Does the date leave enough time? " + "; ".join(parts)
                   + f". If it is a risk, {cite}.")

    saas = [r for r in requirements if _SUPPLIER_HOSTED.search(_text(r))]
    if hosting and saas:
        out.append(f"Hosting model clash: own-premises hosting ({_ids(hosting)}) vs supplier-"
                   f"hosted service ({_ids(saas)}). Can both be true?")

    deleting = [r for r in requirements if _DELETE.search(_text(r))]
    retaining = [r for r in requirements if _RETAIN.search(_text(r)) and r not in deleting]
    both = [r for r in deleting if _RETAIN.search(_text(r))]
    if deleting and (retaining or both):
        out.append(f"Deletion vs retention: must delete or not store ({_ids(deleting)}) vs must "
                   f"keep ({_ids(retaining or both)}). Could the same data fall under both?")

    # Missing information: a bid cannot be planned or priced without these.
    doc_text = doc.text if doc is not None else " ".join(_text(r) for r in requirements)
    # Dates are looked for in the requirements, not the whole document: a "responses due"
    # date on the cover page is not a delivery timeline.
    if not any(r.category == "timeline" or _DATE.search(_text(r)) for r in requirements):
        out.append("Missing timeline: the RFP gives no dates, milestones or go-live target. "
                   "This is a delivery risk and a question for the client.")
    if not _MONEY.search(doc_text):
        out.append("Missing budget: the RFP states no budget or price envelope. This is a "
                   "commercial risk and a question for the client.")

    vague = [(r, m.group(0)) for r in requirements if (m := _VAGUE.search(r.source_quote))
             and not re.search(r"\d", _LABEL.sub("", r.source_quote))]
    if vague:
        listed = "; ".join(f"{r.id} \"{r.title}\" says \"{word}\"" for r, word in vague[:4])
        out.append(f"Undefined targets (no number given): {listed}. These are ambiguity risks "
                   f"unless a measurable target is agreed; name the vague term in the risk.")
    return out


def drop_repeats(ctx: RunContext, drafts: list[RiskDraft]) -> list[RiskDraft]:
    """Small models sometimes fall into a repetition loop and emit the same risk N times
    (failure log F7). Exact repeats (same normalised title) are removed deterministically."""
    seen: set[str] = set()
    out = []
    for d in drafts:
        key = normalize_for_match(d.title)
        if key in seen:
            continue
        seen.add(key)
        out.append(d)
    if len(out) < len(drafts):
        ctx.warn(f"risk analyst repeated itself: dropped {len(drafts) - len(out)} duplicate risk(s)")
    return out


def analyze(ctx: RunContext, requirements: list[Requirement], approach: list[ApproachItem],
            feedback: list[str] | None = None) -> tuple[list[Risk], list[OpenQuestion]]:
    prompt = ctx.prompt(NODE)
    passages = gather_context(ctx)
    hints = conflict_candidates(requirements, ctx.doc)
    if ctx.tracer:
        ctx.tracer.event("conflict_candidates", hints=hints)
    log.info("  risk checklist: %d candidate issue(s)", len(hints))
    log.info("  risk context: %d passages (%s)", len(passages),
             ", ".join(sorted({c.section_id for c in passages})))
    try:
        out = ctx.client.chat_structured(
            prompt.render(requirements=requirements, approach=approach, passages=passages,
                          hints=hints, feedback=feedback or []),
            RiskOutput, node_name=NODE, temperature=ctx.settings.temperature_risk,
            prompt_version=prompt.version)
    except StructuredOutputError as exc:
        ctx.warn(f"risk analysis failed: {exc}")
        return [], []
    valid = {r.id for r in requirements}
    drafts = drop_repeats(ctx, out.risks)
    risks = []
    for i, d in enumerate(drafts, 1):
        ids = normalize_ids(d.related_requirement_ids, valid)
        unknown = [x for x in ids if x not in valid]
        if unknown:  # never fixed by a critic revision in live runs; drop with a warning
            ctx.warn(f"risk '{d.title}' cited unknown requirement ids {unknown}; dropped")
        risks.append(Risk(id=f"R-{i:02d}", **d.model_dump(exclude={"related_requirement_ids"}),
                          related_requirement_ids=[x for x in ids if x in valid]))
    questions = [OpenQuestion(question=q.question, reason=q.reason, raised_by=NODE)
                 for q in out.open_questions]
    return risks, questions
