"""Run the harness over run directories and render a results table (markdown + JSON)."""

from __future__ import annotations

import json
import statistics
from datetime import datetime
from pathlib import Path

from ..ingest import load_document
from .gold import GoldSet, gold_path_for, load_gold
from .scoring import RunScore, consistency, score_run_dir

# (metric key, label, format). Ratios are shown as percentages.
TABLE_ROWS = [
    ("requirements", "Requirements extracted", "int"),
    ("recall_core", "Recall: core gold", "pct"),
    ("recall_must", "Recall: core gold, must", "pct"),
    ("recall_core_lenient", "Recall: core, quoted anywhere", "pct"),
    ("precision", "Precision (matches any gold)", "pct"),
    ("distinct_precision", "Precision, one per obligation", "pct"),
    ("false_positives", "False positives", "int"),
    ("splits", "Split obligations (extra preds)", "int"),
    ("priority_acc", "Priority accuracy (matched core)", "pct"),
    ("grounding_rate", "Grounded quotes", "pct"),
    ("dropped_ungrounded", "Dropped as ungrounded", "int"),
    ("trap_checks_passed", "Trap checks passed", "trap"),
    ("trap_risks_linked", "Planted risks found + cited", "traprisk"),
    ("expected_risks_found", "Expected risks found", "int"),
    ("approach_must_coverage", "Approach covers must reqs", "pct"),
    ("judge_req_faithful", "Judge: requirement faithful", "pct"),
    ("judge_req_priority_ok", "Judge: priority reasonable", "pct"),
    ("judge_approach_specificity", "Judge: approach specificity (1-5)", "float"),
    ("judge_constraint_violations", "Judge: constraint violations", "int"),
    ("judge_risk_specificity", "Judge: risk specificity (1-5)", "float"),
    ("judge_risk_mitigation", "Judge: mitigation quality (1-5)", "float"),
    ("judge_min", "Judge time (min)", "float"),
    ("critic_passed", "Critic passed", "bool"),
    ("revisions", "Revisions", "int"),
    ("wall_min", "Wall time (min)", "float"),
    ("llm_calls", "LLM calls", "int"),
    ("prompt_tokens", "Prompt tokens", "int"),
    ("completion_tokens", "Completion tokens", "int"),
]

NUMERIC = [k for k, _, f in TABLE_ROWS if f in ("int", "pct", "float", "bool")]


def evaluate_runs(run_dirs: list[Path], gold_file: Path | None = None,
                  gold_dir: Path | None = None) -> tuple[GoldSet, list[RunScore]]:
    gold_dir = gold_dir or Path("evals/gold")
    first = _input_file(run_dirs[0]) if run_dirs else None
    gold_file = gold_file or gold_path_for(first or "", gold_dir)
    gold = load_gold(gold_file)
    doc_text = load_document(gold.document).text
    scores = []
    for d in run_dirs:
        inp = _input_file(d)
        if inp and Path(inp).name != Path(gold.document).name:
            s = RunScore(run=d.name, schema_valid=False,
                         error=f"run is for {inp}, gold is for {gold.document}")
        else:
            s = score_run_dir(d, gold, doc_text)
        scores.append(s)
    return gold, scores


def _input_file(run_dir: Path) -> str | None:
    try:
        return json.loads((run_dir / "summary.json").read_text())["metadata"]["input_file"]
    except (OSError, KeyError, ValueError):
        return None


def _fmt(v, kind: str, m: dict) -> str:
    if v is None:
        return "-"
    if kind == "pct":
        return f"{v * 100:.0f}%"
    if kind == "float":
        return f"{v:.2f}" if v < 10 else f"{v:.1f}"
    if kind == "bool":
        return "yes" if v else "no"
    if kind == "trap":
        return f"{v}/{m.get('trap_checks_total', '?')}"
    return f"{v:,}" if isinstance(v, int) else str(v)


def aggregate(scores: list[RunScore]) -> dict[str, dict[str, float]]:
    """Mean and standard deviation of every numeric metric over valid runs."""
    ok = [s for s in scores if s.schema_valid]
    out: dict[str, dict[str, float]] = {}
    for k in NUMERIC:
        vals = [float(s.metrics[k]) for s in ok if s.metrics.get(k) is not None]
        if vals:
            out[k] = {"mean": statistics.fmean(vals),
                      "sd": statistics.stdev(vals) if len(vals) > 1 else 0.0}
    return out


def render_markdown(gold: GoldSet, scores: list[RunScore], title: str = "Eval results") -> str:
    ok = [s for s in scores if s.schema_valid]
    core = sum(1 for g in gold.requirements if g.kind == "core")
    traps = sum(1 for r in gold.risks if r.kind == "trap")
    lines = [f"# {title}", "",
             f"Gold: `{gold.document}` ({core} core / "
             f"{len(gold.requirements) - core} optional requirements, {traps} planted risks; "
             f"status: **{gold.status}**). Generated {datetime.now():%Y-%m-%d %H:%M}.", ""]
    lines += ["| Metric | " + " | ".join(s.run for s in scores) + " |",
              "|---|" + "---:|" * len(scores)]
    lines.append("| Schema valid | " + " | ".join("yes" if s.schema_valid else "**no**"
                                               for s in scores) + " |")
    judged = any("judge_calls_ok" in s.metrics for s in scores)
    for key, label, kind in TABLE_ROWS:
        if key.startswith("judge_") and not judged:
            continue
        cells = []
        for s in scores:
            v = s.metrics.get(key) if s.schema_valid else None
            if kind == "traprisk" and v is not None:
                cells.append(f"{v}/{traps}")
            else:
                cells.append(_fmt(v, kind, s.metrics))
        lines.append(f"| {label} | " + " | ".join(cells) + " |")

    if len(ok) > 1:
        agg = aggregate(ok)
        cons = consistency(ok)
        lines += ["", "## Across runs", "",
                  "| Metric | mean | sd |", "|---|---:|---:|"]
        for key, label, kind in TABLE_ROWS:
            if key in agg:
                a = agg[key]
                scale = 100 if kind == "pct" else 1
                unit = "%" if kind == "pct" else ""
                lines.append(f"| {label} | {a['mean'] * scale:.1f}{unit} | "
                             f"{a['sd'] * scale:.1f}{unit} |")
        if cons:
            lines += ["", f"Consistency: mean pairwise Jaccard of core items found "
                          f"**{cons['mean_pairwise_jaccard']:.2f}**; "
                          f"{cons['core_found_in_all_runs']} core items found in every run, "
                          f"{cons['core_found_in_any_run']} in at least one (of {core})."]

    lines += ["", "## Per-run detail"]
    for s in scores:
        lines += ["", f"### {s.run}", ""]
        if not s.schema_valid:
            lines.append(f"Not scored: {s.error}")
            continue
        lines.append(f"Model `{s.metrics['model']}`; prompts: {s.metrics['prompt_versions']}")
        lines.append("")
        lines.append("Trap checks: " + ", ".join(
            f"{k} {'✓' if v['passed'] else '✗'}" for k, v in s.traps.items()))
        lines.append("")
        lines.append(f"Missed core ({len(s.missed_core)}): "
                     + (", ".join(s.missed_core) or "none"))
        if s.wrong_priority:
            lines.append("")
            lines.append("Wrong priority: " + ", ".join(
                f"{w['gold']} ({w['pred']}: {w['got']}, expected {w['expected']})"
                for w in s.wrong_priority))
        if s.split_groups:
            lines.append("")
            lines.append("Split obligations: " + "; ".join(
                f"{g} → {', '.join(ids)}" for g, ids in sorted(s.split_groups.items())))
        if s.false_positives:
            lines += ["", f"False positives ({len(s.false_positives)}):", ""]
            lines += [f"- {fp['id']} {fp['title']}: \"{fp['quote']}\""
                      for fp in s.false_positives]
    return "\n".join(lines) + "\n"


def write_results(gold: GoldSet, scores: list[RunScore], out_dir: Path, name: str,
                  title: str = "Eval results") -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    md = out_dir / f"{name}.md"
    js = out_dir / f"{name}.json"
    md.write_text(render_markdown(gold, scores, title))
    ok = [s for s in scores if s.schema_valid]
    js.write_text(json.dumps({
        "gold": gold.document, "gold_status": gold.status,
        "runs": [s.to_dict() for s in scores],
        "aggregate": aggregate(ok), "consistency": consistency(ok),
    }, indent=2, default=str))
    return md, js
