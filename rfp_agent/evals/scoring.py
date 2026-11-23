"""Deterministic scoring of one run's ``summary.json`` against a gold set.

Matching
--------
Both predicted and gold requirements carry verbatim quotes. Each quote is located in the
normalised RFP text as a character span; a prediction *matches* a gold requirement when
the spans overlap by at least ``MIN_OVERLAP`` of the shorter span. So a prediction that
quotes a whole paragraph matches every obligation inside it, and a prediction that quotes
half a sentence still matches that sentence.

Metrics (per run)
-----------------
recall_core      share of core gold requirements that some prediction is *about* (its best
                 match, ties broken by title/description similarity). Strict: a paragraph
                 quote counts for one obligation, not every sentence it contains
recall_core_lenient  core gold whose sentence appears in any prediction's quote
recall_must      strict recall, restricted to core gold with priority "must"
precision        share of predictions that match any gold requirement (core or optional);
                 the rest are false positives (context facts, bid-process items, inventions)
distinct_precision  like precision, but extra predictions on an already-covered gold item
                 count as wrong: it penalises splitting one obligation into several
splits           predictions beyond the first on the same gold item
priority_acc     on matched core gold: predicted priority equals the gold priority (or an
                 accepted alternative)
grounding_rate   predictions whose quote verifies against the RFP (score >= 90); always
                 100% on final output because the assembler drops the rest, so
dropped_ungrounded  counts what was dropped
trap_*           planted traps found in risks / open questions, and correctly cited
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from rapidfuzz import fuzz

from ..retrieval import normalize_for_match
from ..schemas import Requirement, SolutionSummary
from .gold import GoldRequirement, GoldSet

MIN_OVERLAP = 0.5  # share of the shorter span that must overlap
MIN_ALIGN_SCORE = 85.0  # fuzzy alignment needed to place a not-quite-verbatim quote
GROUNDED = 90.0


Span = tuple[int, int]


class SpanLocator:
    """Places quotes in the normalised document text (cached per quote)."""

    def __init__(self, doc_text: str):
        self.text = normalize_for_match(doc_text)
        self._cache: dict[str, Span | None] = {}

    def locate(self, quote: str) -> Span | None:
        if quote in self._cache:
            return self._cache[quote]
        nq = normalize_for_match(quote)
        span: Span | None = None
        if len(nq) >= 8:
            i = self.text.find(nq)
            if i >= 0:
                span = (i, i + len(nq))
            else:
                al = fuzz.partial_ratio_alignment(nq, self.text)
                if al is not None and al.score >= MIN_ALIGN_SCORE:
                    span = (al.dest_start, al.dest_end)
        self._cache[quote] = span
        return span


def overlap(a: Span, b: Span) -> float:
    inter = min(a[1], b[1]) - max(a[0], b[0])
    if inter <= 0:
        return 0.0
    return inter / max(1, min(a[1] - a[0], b[1] - b[0]))


@dataclass
class Match:
    pred_id: str
    gold_id: str
    score: float


@dataclass
class RunScore:
    run: str
    schema_valid: bool
    metrics: dict[str, float | int | str | None] = field(default_factory=dict)
    missed_core: list[str] = field(default_factory=list)
    false_positives: list[dict[str, str]] = field(default_factory=list)
    split_groups: dict[str, list[str]] = field(default_factory=dict)
    wrong_priority: list[dict[str, str]] = field(default_factory=list)
    traps: dict[str, dict[str, Any]] = field(default_factory=dict)
    hit_core: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def match_requirements(preds: list[Requirement], gold: list[GoldRequirement],
                       loc: SpanLocator) -> list[Match]:
    """All (prediction, gold) pairs whose quote spans overlap enough."""
    gold_spans = {g.id: [s for s in map(loc.locate, g.spans) if s] for g in gold}
    out: list[Match] = []
    for p in preds:
        ps = loc.locate(p.source_quote)
        if ps is None:
            continue
        for g in gold:
            best = max((overlap(ps, gs) for gs in gold_spans[g.id]), default=0.0)
            if best >= MIN_OVERLAP:
                out.append(Match(p.id, g.id, best))
    return out


def _text_matches(text: str, groups: list[str]) -> bool:
    t = text.lower()
    return all(re.search(g, t) for g in groups)


def score_summary(summary: SolutionSummary, gold: GoldSet, doc_text: str, run: str = ""
                  ) -> RunScore:
    loc = SpanLocator(doc_text)
    preds = summary.requirements
    meta = summary.metadata
    gmap = gold.by_id()
    matches = match_requirements(preds, gold.requirements, loc)

    by_pred: dict[str, list[Match]] = {}
    by_gold: dict[str, list[Match]] = {}
    pred_by_id = {p.id: p for p in preds}
    for m in matches:
        by_pred.setdefault(m.pred_id, []).append(m)
        by_gold.setdefault(m.gold_id, []).append(m)

    # Each prediction is "about" its best-overlapping gold item; extra predictions about the
    # same item are splits (one obligation cut into several requirements).
    # Ties (a paragraph quote fully contains several gold sentences) are broken by how
    # close the prediction's title + description are to each gold quote.
    primary: dict[str, list[str]] = {}
    for pid, ms in by_pred.items():
        p = pred_by_id[pid]
        about = f"{p.title}. {p.description}"
        best = max(ms, key=lambda m: (round(m.score, 2),
                                      fuzz.token_set_ratio(about, gmap[m.gold_id].quote),
                                      gmap[m.gold_id].kind == "core"))
        primary.setdefault(best.gold_id, []).append(pid)
    splits = {g: ids for g, ids in primary.items() if len(ids) > 1}
    n_split = sum(len(ids) - 1 for ids in splits.values())

    core = [g for g in gold.requirements if g.kind == "core"]
    core_must = [g for g in core if g.priority == "must"]
    # Strict: a gold item is found when some prediction is *about* it (its primary match).
    # Lenient: the gold sentence merely appears inside some prediction's quote.
    hit = {g.id for g in core if g.id in primary}
    hit_lenient = {g.id for g in core if g.id in by_gold}
    n = len(preds)
    correct = len(by_pred)

    wrong_priority = []
    pri_ok = 0
    for gid in sorted(hit):
        g = gmap[gid]
        p = pred_by_id[primary[gid][0]]
        if g.priority_ok(p.priority):
            pri_ok += 1
        else:
            wrong_priority.append({"gold": gid, "pred": p.id, "expected": g.priority,
                                   "got": p.priority})

    grounded = sum(1 for p in preds if (p.quote_match_score or 0) >= GROUNDED)

    # --- requirement-level traps ----------------------------------------------------------
    traps: dict[str, dict[str, Any]] = {}
    for gid, want in gold.priority_traps.items():
        ids = primary.get(gid, [])
        got = sorted({pred_by_id[i].priority for i in ids})
        traps[f"priority:{gid}"] = {"passed": bool(ids) and got == [want],
                                    "expected": want, "got": got or "missing"}
    for gid in gold.buried:
        traps[f"buried:{gid}"] = {"passed": gid in primary}
    for pat in gold.forbidden:
        hits = [r.id for r in preds
                if re.search(pat, f"{r.title} {r.description} {r.source_quote}", re.I)]
        hits += [f"A{i}" for i, a in enumerate(summary.approach, 1)
                 if re.search(pat, f"{a.summary} {' '.join(a.components)} {a.rationale}", re.I)]
        traps[f"forbidden:{pat}"] = {"passed": not hits, "in": hits}

    # --- risks -------------------------------------------------------------------------
    golds_of_pred = {pid: {m.gold_id for m in ms} for pid, ms in by_pred.items()}
    risk_results: dict[str, dict[str, Any]] = {}
    for gr in gold.risks:
        found_in, linked = [], False
        for r in summary.risks:
            if _text_matches(f"{r.title} {r.description} {r.mitigation}", gr.all_of):
                found_in.append(r.id)
                cited = set().union(*(golds_of_pred.get(i, set())
                                      for i in r.related_requirement_ids))
                linked = linked or set(gr.cites) <= cited
        if gr.where == "risks_or_questions":
            for i, q in enumerate(summary.open_questions):
                if _text_matches(f"{q.question} {q.reason}", gr.all_of):
                    found_in.append(f"Q{i + 1}")
            linked = linked or (bool(found_in) and not gr.cites)
        risk_results[gr.id] = {"kind": gr.kind, "found": bool(found_in), "linked": linked,
                               "in": found_in}
    traps.update({f"risk:{k}": {"passed": v["found"] and v["linked"], **v}
                  for k, v in risk_results.items() if v["kind"] == "trap"})
    trap_risks = [v for v in risk_results.values() if v["kind"] == "trap"]
    exp_risks = [v for v in risk_results.values() if v["kind"] == "expected"]

    # --- approach ------------------------------------------------------------------------
    covered = {i for a in summary.approach for i in a.requirement_ids}
    musts = [p.id for p in preds if p.priority == "must"]

    wall = ((meta.finished_at - meta.started_at).total_seconds() / 60
            if meta.finished_at else None)
    usage = meta.usage or {}

    metrics: dict[str, float | int | str | None] = {
        "requirements": n,
        "recall_core": _ratio(len(hit), len(core)),
        "recall_must": _ratio(len(hit & {g.id for g in core_must}), len(core_must)),
        "recall_core_lenient": _ratio(len(hit_lenient), len(core)),
        "precision": _ratio(correct, n),
        "distinct_precision": _ratio(correct - n_split, n),
        "false_positives": n - correct,
        "splits": n_split,
        "priority_acc": _ratio(pri_ok, len(hit)),
        "grounding_rate": _ratio(grounded, n),
        "dropped_ungrounded": len(meta.dropped_requirements),
        "trap_checks_passed": sum(1 for t in traps.values() if t["passed"]),
        "trap_checks_total": len(traps),
        "trap_risks_found": sum(1 for v in trap_risks if v["found"]),
        "trap_risks_linked": sum(1 for v in trap_risks if v["found"] and v["linked"]),
        "expected_risks_found": sum(1 for v in exp_risks if v["found"]),
        "risks": len(summary.risks),
        "approach_items": len(summary.approach),
        "approach_must_coverage": _ratio(len(set(musts) & covered), len(musts)),
        "open_questions": len(summary.open_questions),
        "critic_passed": int(meta.critic_passed),
        "revisions": meta.revisions,
        "wall_min": round(wall, 1) if wall is not None else None,
        "llm_calls": int(usage.get("calls", 0)),
        "prompt_tokens": int(usage.get("prompt_tokens", 0)),
        "completion_tokens": int(usage.get("completion_tokens", 0)),
        "model": meta.model,
        "prompt_versions": ", ".join(f"{k}={v}" for k, v in sorted(meta.prompt_versions.items())),
    }
    return RunScore(
        run=run or meta.run_id, schema_valid=True, metrics=metrics,
        missed_core=sorted(g.id for g in core if g.id not in hit),
        false_positives=[{"id": p.id, "title": p.title, "quote": p.source_quote[:90]}
                         for p in preds if p.id not in by_pred],
        split_groups=splits, wrong_priority=wrong_priority, traps=traps, hit_core=sorted(hit))


def score_run_dir(run_dir: Path, gold: GoldSet, doc_text: str) -> RunScore:
    path = Path(run_dir) / "summary.json"
    try:
        summary = SolutionSummary.model_validate(json.loads(path.read_text()))
    except FileNotFoundError:
        return RunScore(run=Path(run_dir).name, schema_valid=False, error="no summary.json")
    except (ValidationError, json.JSONDecodeError) as exc:
        return RunScore(run=Path(run_dir).name, schema_valid=False,
                        error=f"invalid summary.json: {str(exc)[:200]}")
    return score_summary(summary, gold, doc_text, run=Path(run_dir).name)


def consistency(scores: list[RunScore]) -> dict[str, float]:
    """Agreement between runs: mean pairwise Jaccard of the core gold items each run found,
    and the share of core items found in every run vs. in at least one."""
    sets = [set(s.hit_core) for s in scores if s.schema_valid]
    if len(sets) < 2:
        return {}
    pairs = [(a, b) for i, a in enumerate(sets) for b in sets[i + 1:]]
    jac = sum(len(a & b) / max(1, len(a | b)) for a, b in pairs) / len(pairs)
    union, inter = set().union(*sets), set.intersection(*sets)
    return {"runs": len(sets), "mean_pairwise_jaccard": round(jac, 3),
            "core_found_in_all_runs": len(inter), "core_found_in_any_run": len(union)}


def _ratio(a: int, b: int) -> float | None:
    return round(a / b, 3) if b else None
