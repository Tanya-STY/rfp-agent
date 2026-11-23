"""Requirements extraction: LLM map over section batches + deterministic reduce.

map:    pack sections into batches that fit a small context -> one LLM call per batch
ground: verify / snap every quote against the source (deterministic)
reduce: merge duplicates (embedding similarity + identical quotes) and assign ids
        (deterministic - an LLM is not needed, and would be slower and less repeatable)
"""

from __future__ import annotations

import logging
import re

from ..context import RunContext
from ..ingest import Document, Section
from ..llm import OutputTruncatedError, StructuredOutputError
from ..retrieval import CLUSTER_PREFIX, cosine_matrix, normalize_for_match, snap_quote
from ..schemas import CATEGORY_PREFIX, ExtractionOutput, OpenQuestion, Requirement

log = logging.getLogger("rfp_agent")
NODE = "extract_requirements"
_PRIORITY_RANK = {"must": 0, "should": 1, "could": 2}
_CATEGORY_ORDER = list(CATEGORY_PREFIX)


def pack_batches(sections: list[Section], max_chars: int) -> list[list[Section]]:
    """Greedy, order-preserving packing of consecutive sections up to max_chars."""
    batches: list[list[Section]] = []
    cur: list[Section] = []
    size = 0
    for s in sections:
        n = len(s.render())
        if cur and size + n > max_chars:
            batches.append(cur)
            cur, size = [], 0
        cur.append(s)
        size += n
    if cur:
        batches.append(cur)
    return batches


def skipped_section_ids(sections: list[Section], pattern: str) -> set[str]:
    """Ids of bidding-process sections (submission instructions, evaluation criteria)."""
    if not pattern:
        return set()
    rx = re.compile(pattern, re.I)
    return {s.id for s in sections if rx.search(s.title)}


def extract(ctx: RunContext, sections: list[Section], feedback: list[str] | None = None
            ) -> tuple[list[Requirement], list[OpenQuestion]]:
    batches = pack_batches(sections, ctx.settings.extract_batch_chars)
    reqs: list[Requirement] = []
    questions: list[OpenQuestion] = []
    for i, batch in enumerate(batches, 1):
        log.info("  extract batch %d/%d: sections %s", i, len(batches),
                 ", ".join(s.id for s in batch))
        r, q = _extract_batch(ctx, batch, feedback or [])
        reqs += r
        questions += q
    assert ctx.doc is not None
    thr = ctx.settings.quote_match_threshold
    reqs = [ground(r, ctx.doc, thr) for r in reqs]
    reqs = split_multi_sentence(ctx, reqs)
    reqs = drop_context_facts(ctx, reqs)
    reqs = calibrate_priority(ctx, reqs)
    return align_description_modal(ctx, reqs), questions


def _extract_batch(ctx: RunContext, batch: list[Section], feedback: list[str], depth: int = 0
                   ) -> tuple[list[Requirement], list[OpenQuestion]]:
    prompt = ctx.prompt(NODE)
    ids = [s.id for s in batch]
    try:
        out = ctx.client.chat_structured(
            prompt.render(sections=batch, feedback=feedback), ExtractionOutput,
            node_name=NODE, temperature=ctx.settings.temperature_extract,
            prompt_version=prompt.version)
    except OutputTruncatedError:
        # Too many requirements for one answer: split the batch and try each half.
        halves = _split_batch(batch)
        if depth >= 2 or halves is None:
            ctx.warn(f"extraction batch {ids} truncated and cannot be split further")
            return [], []
        ctx.warn(f"extraction batch {ids} truncated; splitting in two")
        r1, q1 = _extract_batch(ctx, halves[0], feedback, depth + 1)
        r2, q2 = _extract_batch(ctx, halves[1], feedback, depth + 1)
        return r1 + r2, q1 + q2
    except StructuredOutputError as exc:
        # Degrade gracefully: one bad batch should not kill the run. The critic's
        # numbered-coverage check will usually notice the gap and request a redo.
        ctx.warn(f"extraction batch {ids} failed: {exc}")
        return [], []
    reqs = []
    for d in out.requirements:
        section_id = d.section_id if d.section_id in ids else ids[0]
        reqs.append(Requirement(
            id="tmp", title=d.title, description=d.description, category=d.category,
            priority=d.priority, source_section=section_id, source_quote=d.source_quote,
            confidence=d.confidence))
    questions = [OpenQuestion(question=q.question, reason=q.reason, raised_by=NODE)
                 for q in out.open_questions]
    return reqs, questions


def _split_batch(batch: list[Section]) -> tuple[list[Section], list[Section]] | None:
    if len(batch) > 1:
        mid = len(batch) // 2
        return batch[:mid], batch[mid:]
    s = batch[0]
    paras = [p for p in s.text.split("\n\n") if p.strip()]
    if len(paras) < 2:
        return None
    mid = len(paras) // 2
    return ([s.model_copy(update={"text": "\n\n".join(paras[:mid])})],
            [s.model_copy(update={"text": "\n\n".join(paras[mid:])})])


_MODALS = {
    "must": re.compile(r"\b(shall|must|required|mandatory|is fixed|will not be considered"
                       r"|not permitted|not allowed|prohibited)\b", re.I),
    "should": re.compile(r"\b(should|expected|expects|prefers?|preferably)\b", re.I),
    "could": re.compile(r"\b(would be welcome|nice to have|optional|if possible)\b", re.I),
}


def priority_from_quote(quote: str) -> str | None:
    """MoSCoW priority implied by the modal verbs in the quote, if unambiguous.

    Returns None when the quote has no modal (implied requirement) or mixes classes
    ("shall ... should"), in which case the model's judgement is kept.
    """
    hits = [p for p, rx in _MODALS.items() if rx.search(quote)]
    return hits[0] if len(hits) == 1 else None


def has_obligation(quote: str) -> bool:
    return any(rx.search(quote) for rx in _MODALS.values())


def drop_context_facts(ctx: RunContext, reqs: list[Requirement]) -> list[Requirement]:
    """In context sections (current environment, background...) keep only requirements
    whose quote states an obligation. The model turns descriptions such as "The Company
    operates two data centres" into must-requirements despite the prompt (F4, F19).
    Implied requirements in other sections are not affected."""
    pattern = ctx.settings.context_section_titles
    if not pattern or ctx.doc is None:
        return reqs
    rx = re.compile(pattern, re.I)
    context = {s.id for s in ctx.doc.sections if rx.search(s.title)}
    kept, dropped = [], []
    for r in reqs:
        if r.source_section in context and not has_obligation(r.source_quote):
            dropped.append(r.title)
        else:
            kept.append(r)
    if dropped:
        ctx.tracer.event("context_facts_dropped", titles=dropped)
        log.info("  dropped %d context fact(s) from context sections", len(dropped))
    return kept


def calibrate_priority(ctx: RunContext, reqs: list[Requirement]) -> list[Requirement]:
    """Deterministic override: small models over-assign "must" (failure log F2/F4)."""
    out, changed = [], []
    for r in reqs:
        p = priority_from_quote(r.source_quote)
        if p and p != r.priority:
            changed.append((r.title, r.priority, p))
            r = r.model_copy(update={"priority": p})
        out.append(r)
    if changed:
        ctx.tracer.event("priority_calibration", changed=changed)
        log.info("  priority calibrated from modal verbs on %d requirement(s)", len(changed))
    return out


# ------------------------------------------------------------------ description modals

_STRONG = re.compile(r"\b(must|shall)\b", re.I)
_REQUIRED = re.compile(r"\b(is|are) required\b", re.I)


def align_description_modal(ctx: RunContext, reqs: list[Requirement]) -> list[Requirement]:
    """A "should"/"could" requirement must not be described with "must" (phase 2 finding 3:
    the judge found 'should describe' -> 'must describe'). Only applied when the quote
    itself has no must-class modal, so a description is never weakened below its source."""
    out, changed = [], []
    for r in reqs:
        if r.priority != "must" and not _MODALS["must"].search(r.source_quote):
            word = r.priority
            d = _STRONG.sub(word, r.description)
            d = _REQUIRED.sub(lambda m: f"{m.group(1)} expected" if word == "should"
                              else f"{m.group(1)} optional", d)
            if d != r.description:
                changed.append(r.title)
                r = r.model_copy(update={"description": d})
        out.append(r)
    if changed:
        ctx.tracer.event("description_modal_aligned", titles=changed)
    return out


# ------------------------------------------------------------- one obligation per quote

_SENTENCE_END = re.compile(r"[.!?](?:\*\*)?(?=\s+[A-Z\"(*])")
_MIN_SENTENCE_CHARS = 25


def sentences(text: str) -> list[str]:
    """Split a verbatim quote into its sentences (each still a verbatim span)."""
    out, start = [], 0
    for m in _SENTENCE_END.finditer(text):
        out.append(text[start:m.end()].strip())
        start = m.end()
    out.append(text[start:].strip())
    return [x for x in out if x]


_CLAUSE_SPLIT = re.compile(r";\s+(?:(?:however|but|whereas|although|while)\s*,?\s+)?", re.I)


def obligation_parts(text: str) -> list[str]:
    """Sentences of a quote, with a sentence split again at a semicolon when both sides
    state their own obligation ("Corvane expects a blended team; however, any personnel
    with access to production data must be based in Malaysia"). Two modals in one
    sentence are two obligations, often with different priorities; kept together, dedupe
    merged them into one "should" requirement and the "must" was lost. Each part is
    still a verbatim span of the RFP."""
    out = []
    for s in sentences(text):
        parts = [p.strip() for p in _CLAUSE_SPLIT.split(s) if p.strip()]
        if len(parts) > 1 and all(has_obligation(p) and len(p) >= _MIN_SENTENCE_CHARS
                                  for p in parts):
            out += parts
        else:
            out.append(s)
    return out


def _about(r: Requirement) -> str:
    return f"{r.title}. {r.description}"


def _orphan_title(sentence: str) -> str:
    s = _LEADING_LABEL.sub("", sentence).strip("*# ")
    s = re.sub(r"^\**[A-Z]{2,5}-\d{1,3}\**\s*", "", s).strip("*# ")  # bare label "INT-2**"
    s = re.sub(r"^(the (solution|service|supplier|bidder|assistant|platform)|bidders)\s+"
               r"(shall|must|should|may)( not)?\s+", lambda m: "Not " if m.group(4) else "",
               s, flags=re.I)
    words = s.rstrip(".").split()
    title = " ".join(words[:8])
    return title[:1].upper() + title[1:]


def split_multi_sentence(ctx: RunContext, reqs: list[Requirement]) -> list[Requirement]:
    """One obligation per quote (phase 2 finding 2).

    The model often quotes a whole paragraph ("FR-7 ... shall identify fraud indicators.
    The solution must never automatically decline a claim.") but its title and
    description cover one sentence, so the second obligation is invisible downstream.
    The quote is trimmed to the sentence that best matches the title/description; every
    other sentence that states an obligation (modal verb) and is not already some other
    requirement's quote becomes its own requirement, titled from its first words.
    All quotes stay verbatim spans, so grounding is unaffected.
    """
    from rapidfuzz import fuzz

    thr = ctx.settings.quote_match_threshold
    assert ctx.doc is not None
    out: list[Requirement] = []
    orphans: list[tuple[Requirement, str]] = []
    for r in reqs:
        parts = [x for x in obligation_parts(r.source_quote) if len(x) >= _MIN_SENTENCE_CHARS]
        if (r.quote_match_score or 0) < thr or len(parts) < 2:
            out.append(r)
            continue
        best = max(parts, key=lambda x: fuzz.token_set_ratio(_about(r), x))
        out.append(r.model_copy(update={"source_quote": best}))
        orphans += [(r, x) for x in parts if x != best and has_obligation(x)]

    covered = [normalize_for_match(r.source_quote) for r in out]
    added = []
    for parent, sent in orphans:
        n = normalize_for_match(sent)
        if any(n in c or c in n for c in covered if c):
            continue
        covered.append(n)
        new = Requirement(id="tmp", title=_orphan_title(sent), description=sent,
                          category=parent.category, priority=priority_from_quote(sent)
                          or parent.priority, source_section=parent.source_section,
                          source_quote=sent, confidence=min(parent.confidence, 0.7))
        added.append(ground(new, ctx.doc, thr))
    trimmed = sum(1 for a, b in zip(reqs, out) if a.source_quote != b.source_quote)
    if trimmed or added:
        ctx.tracer.event("quote_split", trimmed=trimmed, added=[a.title for a in added])
        log.info("  quotes trimmed to one sentence: %d; obligations split out: %d",
                 trimmed, len(added))
    return out + added


_LEADING_LABEL = re.compile(r"^\W*[A-Z]{2,5}-\d{1,3}\b[^.:]{0,60}[.:]\W*")
_LIST_MARKER = re.compile(r"(?:^|\s)(?:\d{1,2}[.)]|[-*•])\s+")
_MIN_RESCUE_CHARS = 25


def stitch_candidates(quote: str) -> list[str]:
    """Verbatim pieces of a quote the model stitched together (failure log F12, F14).

    Small models glue a list lead-in or a requirement label onto a later sentence:
    "Proposals should contain: 2. A requirements compliance matrix ..." or
    "**NFR-3 Availability.** Planned maintenance must be ...". The tail after the label,
    the last list marker or the last colon is often an exact span on its own.
    """
    q = quote.strip()
    out = []
    for cand in (_LEADING_LABEL.sub("", q), _LIST_MARKER.split(q)[-1], q.rsplit(":", 1)[-1]):
        cand = cand.strip()
        if len(cand) >= _MIN_RESCUE_CHARS and cand != q and cand not in out:
            out.append(cand)
    return out


def _snap_with_rescue(quote: str, source: str, threshold: float):
    q, m = snap_quote(quote, source, threshold)
    if m.ok(threshold):
        return q, m
    for cand in stitch_candidates(quote):
        cq, cm = snap_quote(cand, source, threshold)
        if cm.ok(threshold):
            return cq, cm
    return q, m


def ground(req: Requirement, doc: Document, threshold: float) -> Requirement:
    """Verify the quote; snap near-misses to the exact source span; fix the section id."""
    section = doc.section(req.source_section)
    if section is not None:
        quote, m = _snap_with_rescue(req.source_quote, section.text, threshold)
        if m.ok(threshold):
            return req.model_copy(update={"source_quote": quote, "quote_match_score": m.score})
    # Not in the claimed section: the model may have mislabelled the section.
    quote, m = _snap_with_rescue(req.source_quote, doc.text, threshold)
    update: dict = {"source_quote": quote, "quote_match_score": m.score}
    if m.ok(threshold):
        needle = normalize_for_match(quote)
        for s in doc.sections:
            if needle in normalize_for_match(s.text):
                update["source_section"] = s.id
                break
    return req.model_copy(update=update)


def _distinct_sentences(a: Requirement, b: Requirement, qa: str, qb: str) -> bool:
    """Two different obligation sentences from the same section are two requirements,
    however similar their titles look to the embedder. split_multi_sentence creates exactly
    such pairs ("Lookups shall use IBM MQ." / "The solution shall not write to the policy
    system."), and similarity-merging them undid the split (phase 2b: INT-2b lost).
    Duplicates across sections (a scope bullet vs the numbered requirement, F8) still merge."""
    return (a.source_section == b.source_section and bool(qa) and bool(qb)
            and qa not in qb and qb not in qa
            and has_obligation(a.source_quote) and has_obligation(b.source_quote))


def dedupe_and_number(ctx: RunContext, reqs: list[Requirement]) -> list[Requirement]:
    """Merge near-duplicates and assign stable, category-prefixed ids (FR-01, SEC-02...)."""
    if not reqs:
        return []
    thr = ctx.settings.quote_match_threshold
    vecs = ctx.client.embed([CLUSTER_PREFIX + f"{r.title}. {r.description}" for r in reqs],
                            node_name=NODE)
    sim = cosine_matrix(vecs)
    quotes = [normalize_for_match(r.source_quote) for r in reqs]

    parent = list(range(len(reqs)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(reqs)):
        for j in range(i + 1, len(reqs)):
            # Same quote alone is NOT enough: the model sometimes derives two distinct
            # obligations from one quote ("Bahasa expected... Chinese welcome"), which
            # must stay separate (failure log F11). Same quote + related meaning merges.
            # Same quote AND same priority is one obligation split into parts (one
            # sentence -> 5 requirements in run 7, F19); the prompt already forbids
            # sharing a quote. Different priorities on one quote stay apart.
            same_quote = bool(quotes[i]) and quotes[i] == quotes[j] and (
                sim[i, j] >= 0.85 or reqs[i].priority == reqs[j].priority)
            if same_quote or (sim[i, j] >= ctx.settings.dedupe_similarity
                              and not _distinct_sentences(reqs[i], reqs[j], quotes[i], quotes[j])):
                parent[find(j)] = find(i)

    clusters: dict[int, list[int]] = {}
    for i in range(len(reqs)):
        clusters.setdefault(find(i), []).append(i)

    def quality(i: int) -> tuple:
        r = reqs[i]
        grounded = (r.quote_match_score or 0) >= thr
        # Prefer grounded, then the more specific (longer) quote - e.g. the numbered
        # "FR-7 ..." paragraph over a one-line scope bullet saying the same thing, so
        # the labelled requirement stays traceable (failure log F8) - then confidence.
        return (not grounded, -len(r.source_quote), -r.confidence)

    kept: list[Requirement] = []
    for members in clusters.values():
        best = min(members, key=quality)
        r = reqs[best]
        # A merged requirement takes the strongest priority among its duplicates.
        top_priority = min((reqs[m].priority for m in members), key=_PRIORITY_RANK.get)
        parts = []
        for m in members:
            t = reqs[m].title
            if (m != best and quotes[m] == quotes[best] and t.lower() != r.title.lower()
                    and t not in parts):
                parts.append(t)
        update = {"priority": top_priority}
        if parts:
            update["description"] = f"{r.description} Also covers: {'; '.join(parts)}."
        kept.append(r.model_copy(update=update))
    if ctx.tracer:
        ctx.tracer.event("dedupe", before=len(reqs), after=len(kept),
                         merged=[[reqs[m].title for m in ms] for ms in clusters.values()
                                 if len(ms) > 1])
    log.info("  dedupe: %d -> %d requirements", len(reqs), len(kept))
    return number(kept, ctx.doc)


def number(reqs: list[Requirement], doc: Document | None) -> list[Requirement]:
    """Deterministic ids: by category, then by position of the quote in the document."""
    def pos(r: Requirement) -> int:
        if doc is None:
            return 0
        idx = doc.text.find(r.source_quote)
        return idx if idx >= 0 else len(doc.text)

    ordered = sorted(reqs, key=lambda r: (_CATEGORY_ORDER.index(r.category), pos(r)))
    counters: dict[str, int] = {}
    out = []
    for r in ordered:
        prefix = CATEGORY_PREFIX[r.category]
        counters[prefix] = counters.get(prefix, 0) + 1
        out.append(r.model_copy(update={"id": f"{prefix}-{counters[prefix]:02d}"}))
    return out
