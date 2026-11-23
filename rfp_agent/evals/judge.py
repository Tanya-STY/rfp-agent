"""LLM-as-judge: rubric scores for what the deterministic metrics cannot see.

The deterministic scorer (``scoring.py``) already measures recall, precision, priorities,
traps and risk links against the gold set. The judge adds *quality* judgments:

* requirement faithfulness - does the title/description say what the quote says?
* approach specificity (1-5) and hard-constraint violations (constraints from the gold file)
* risk specificity and mitigation actionability (1-5)

Design choices (see prompts/judge_*.md):
* one small judgment per call - local 7-9B models are unreliable on whole reports;
* a different model family from the pipeline (llama3.1:8b vs qwen2.5:7b);
* every judgment is saved with an empty ``human`` field so Tanya can label a subset and
  ``calibrate`` reports how often the judge agrees with her.
"""

from __future__ import annotations

import json
import random
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from ..config import Settings
from ..llm import LLMClient, StructuredOutputError
from ..prompts import load_prompt
from ..schemas import SolutionSummary
from ..tracing import Tracer, activate
from .gold import GoldSet

NODE = "judge"


class RequirementVerdict(BaseModel):
    faithful: bool
    priority_ok: bool
    reason: str = ""


class ApproachVerdict(BaseModel):
    specificity: int = Field(ge=1, le=5)
    violates_constraint: bool
    violated: str = ""
    reason: str = ""


class RiskVerdict(BaseModel):
    specificity: int = Field(ge=1, le=5)
    mitigation: int = Field(ge=1, le=5)
    reason: str = ""


@dataclass
class Judgment:
    run: str
    kind: str  # requirement | approach | risk
    item: str  # requirement id / approach index / risk id
    verdict: dict[str, Any]
    prompt_version: str
    model: str

    def to_json(self) -> dict[str, Any]:
        return {"run": self.run, "kind": self.kind, "item": self.item,
                "judge": self.verdict, "human": None, "prompt_version": self.prompt_version,
                "model": self.model}


def sample_requirements(summary: SolutionSummary, n: int, seed: int = 0):
    reqs = sorted(summary.requirements, key=lambda r: r.id)
    if len(reqs) <= n:
        return reqs
    return sorted(random.Random(seed).sample(reqs, n), key=lambda r: r.id)


def judge_summary(summary: SolutionSummary, gold: GoldSet, client: LLMClient,
                  settings: Settings, run: str) -> list[Judgment]:
    """All judgments for one run. Failed calls are skipped (and traced), never fatal."""
    pdir = str(settings.prompts_dir)
    t = settings.temperature_judge
    by_id = {r.id: r for r in summary.requirements}
    out: list[Judgment] = []

    def ask(prompt_name: str, schema, kind: str, item: str, **kw) -> None:
        p = load_prompt(prompt_name, pdir)
        try:
            v = client.chat_structured(p.render(**kw), schema, NODE, temperature=t,
                                       prompt_version=p.version)
        except StructuredOutputError:
            return
        out.append(Judgment(run, kind, item, v.model_dump(), p.version, client.model))

    for r in sample_requirements(summary, settings.judge_sample_requirements):
        ask("judge_requirement", RequirementVerdict, "requirement", r.id, quote=r.source_quote,
            title=r.title, description=r.description, priority=r.priority)
    for i, a in enumerate(summary.approach, 1):
        quotes = [by_id[x].source_quote[:300] for x in a.requirement_ids if x in by_id][:8]
        ask("judge_approach", ApproachVerdict, "approach", f"A{i}", constraints=gold.constraints,
            quotes=quotes, summary=a.summary, components=a.components, rationale=a.rationale)
    for k in summary.risks:
        quotes = [by_id[x].source_quote[:300] for x in k.related_requirement_ids if x in by_id]
        ask("judge_risk", RiskVerdict, "risk", k.id, quotes=quotes, title=k.title,
            description=k.description, category=k.category, likelihood=k.likelihood,
            impact=k.impact, mitigation=k.mitigation)
    return out


def judge_metrics(judgments: list[Judgment]) -> dict[str, float | int | None]:
    def verdicts(kind: str) -> list[dict[str, Any]]:
        return [j.verdict for j in judgments if j.kind == kind]

    def share(vs, key):
        return round(sum(bool(v[key]) for v in vs) / len(vs), 3) if vs else None

    def mean(vs, key):
        return round(statistics.fmean(v[key] for v in vs), 2) if vs else None

    req, app, risk = verdicts("requirement"), verdicts("approach"), verdicts("risk")
    return {
        "judge_req_faithful": share(req, "faithful"),
        "judge_req_priority_ok": share(req, "priority_ok"),
        "judge_approach_specificity": mean(app, "specificity"),
        "judge_constraint_violations": sum(bool(v["violates_constraint"]) for v in app),
        "judge_risk_specificity": mean(risk, "specificity"),
        "judge_risk_mitigation": mean(risk, "mitigation"),
        "judge_calls_ok": len(judgments),
    }


def run_judge(summary: SolutionSummary, gold: GoldSet, client: LLMClient, settings: Settings,
              run: str, trace_dir: Path) -> tuple[list[Judgment], dict[str, float | int | None],
                                                  dict[str, float]]:
    tracer = Tracer(f"judge-{run}", trace_dir)
    with activate(tracer):
        judgments = judge_summary(summary, gold, client, settings, run)
    return judgments, judge_metrics(judgments), tracer.totals()


# ------------------------------------------------------------------------------- calibration

def calibrate(path: Path) -> dict[str, Any]:
    """Agreement between the judge and human labels in a judgments.jsonl file.

    A row is labelled when its ``human`` field holds the same keys as ``judge`` (fill in
    only the ones you checked). Booleans: share of agreement. 1-5 scores: share within one
    point, and mean absolute difference.
    """
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    labelled = [r for r in rows if isinstance(r.get("human"), dict)]
    report: dict[str, Any] = {"rows": len(rows), "labelled": len(labelled), "fields": {}}
    fields: dict[str, list[tuple[Any, Any]]] = {}
    for r in labelled:
        for k, hv in r["human"].items():
            if k in r["judge"] and k not in ("reason", "violated") and hv is not None:
                fields.setdefault(f"{r['kind']}.{k}", []).append((r["judge"][k], hv))
    for k, pairs in sorted(fields.items()):
        if all(isinstance(h, bool) for _, h in pairs):
            agree = sum(bool(j) == h for j, h in pairs) / len(pairs)
            report["fields"][k] = {"n": len(pairs), "agreement": round(agree, 3)}
        else:
            diffs = [abs(float(j) - float(h)) for j, h in pairs]
            report["fields"][k] = {"n": len(pairs),
                                   "within_1": round(sum(d <= 1 for d in diffs) / len(diffs), 3),
                                   "mean_abs_diff": round(statistics.fmean(diffs), 2)}
    return report
