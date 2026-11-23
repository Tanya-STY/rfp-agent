"""Cost report: what a run cost locally ($0) and what it *would* cost on a hosted model.

Reads the ``llm_call`` lines of ``runs/<id>/trace.jsonl`` (written by ``record_call``), so
it works for any past run without re-running anything.

Caveats, stated in the report too:
* Token counts come from the local model's tokenizer (qwen2.5). Claude tokenizers count
  the same text differently (Haiku 5.5's is ~30% higher), so hosted figures are estimates.
* Hosted models with thinking enabled add output tokens we cannot know in advance; the
  estimate covers the visible output only.
* Embeddings are priced at $0: a hosted embedding API costs cents per million tokens,
  well below the rounding of this report.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

# USD per 1M tokens (input, output). Source: Anthropic model list, Nov 2026.
HOSTED_PRICES: dict[str, tuple[float, float]] = {
    "Claude Haiku 5.5": (0.10, 0.50),
    "Claude Sonnet 5.5": (2.00, 10.00),
    "Claude Opus 5.5": (4.00, 20.00),
}
TOKENIZER_NOTE = ("Tokens are counted by the local model's tokenizer; hosted tokenizers differ "
                  "(Haiku 5.5 counts ~30% more), and thinking tokens are not included.")


def load_calls(run_dir: Path) -> list[dict]:
    path = Path(run_dir) / "trace.jsonl"
    rows = []
    for line in path.read_text().splitlines():
        if '"llm_call"' in line:
            r = json.loads(line)
            if r.get("type") == "llm_call":
                rows.append(r)
    return rows


def run_costs(run_dir: Path) -> dict:
    calls = load_calls(run_dir)
    nodes: dict[str, dict[str, float]] = defaultdict(
        lambda: {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "latency_s": 0.0})
    for c in calls:
        if c["kind"] != "chat":
            continue
        n = nodes[c["node"]]
        n["calls"] += 1
        n["prompt_tokens"] += c["prompt_tokens"]
        n["completion_tokens"] += c["completion_tokens"]
        n["latency_s"] += c["latency_ms"] / 1000
    total = {k: sum(n[k] for n in nodes.values())
             for k in ("calls", "prompt_tokens", "completion_tokens", "latency_s")}
    hosted = {m: hosted_cost(total["prompt_tokens"], total["completion_tokens"], m)
              for m in HOSTED_PRICES}
    return {"run": Path(run_dir).name, "nodes": dict(nodes), "total": total, "hosted": hosted,
            "models": sorted({c["model"] for c in calls if c["kind"] == "chat"})}


def hosted_cost(prompt_tokens: float, completion_tokens: float, model: str) -> float:
    p_in, p_out = HOSTED_PRICES[model]
    return (prompt_tokens * p_in + completion_tokens * p_out) / 1e6


def render_markdown(reports: list[dict], monthly_rfps: int = 50) -> str:
    out = ["# Cost report", "",
           "Local runs on Ollama cost **$0** in API fees (electricity and hardware aside).",
           "The hosted columns show what the same token volume would cost on Claude.", "",
           f"_{TOKENIZER_NOTE}_", ""]
    models = list(HOSTED_PRICES)
    out.append("| Run | LLM calls | Input tok | Output tok | Model time (min) | "
               + " | ".join(models) + " |")
    out.append("|---|---|---|---|---|" + "---|" * len(models))
    for r in reports:
        t = r["total"]
        out.append(f"| {r['run']} | {t['calls']} | {t['prompt_tokens']:,} | "
                   f"{t['completion_tokens']:,} | {t['latency_s'] / 60:.1f} | "
                   + " | ".join(f"${r['hosted'][m]:.3f}" for m in models) + " |")
    if reports:
        avg = {m: sum(r["hosted"][m] for r in reports) / len(reports) for m in models}
        out += ["", f"**At {monthly_rfps} RFPs a month** (average of the runs above): "
                + ", ".join(f"{m} ${avg[m] * monthly_rfps:.2f}" for m in models) + "."]
        out += ["", "## Where the tokens go (first run)", "",
                "| Node | Calls | Input tok | Output tok | Model time (s) | Share of cost* |",
                "|---|---|---|---|---|---|"]
        r = reports[0]
        cost = {n: hosted_cost(v["prompt_tokens"], v["completion_tokens"], models[0])
                for n, v in r["nodes"].items()}
        whole = sum(cost.values()) or 1
        for n, v in sorted(r["nodes"].items(), key=lambda kv: -cost[kv[0]]):
            out.append(f"| {n} | {v['calls']} | {v['prompt_tokens']:,} | "
                       f"{v['completion_tokens']:,} | {v['latency_s']:.0f} | "
                       f"{cost[n] / whole:.0%} |")
        out += ["", f"*share of the {models[0]} cost; the split is the same for any model "
                "whose output/input price ratio is 5x."]
    return "\n".join(out) + "\n"
