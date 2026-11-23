"""Command line entry point.

    python -m rfp_agent run --input inputs/rfp_synthetic_main.md [--model qwen2.5:7b] [--run-id X]
    python -m rfp_agent eval ...     (see README "Evaluate")
    python -m rfp_agent cost runs/<id> [...] [--out evals/results/cost.md]
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
import uuid
from datetime import datetime

from .config import get_settings
from .context import RunContext
from .graph import build_graph, initial_state
from .llm import LLMClient, make_client
from .tracing import Tracer, activate


def run(input_path: str, run_id: str | None = None, client: LLMClient | None = None,
        **overrides) -> tuple[str, Tracer]:
    """Run the full graph. Returns (summary.json path, tracer). Used by CLI and tests."""
    settings = get_settings(**overrides)
    run_id = run_id or f"{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}"
    tracer = Tracer(run_id, settings.runs_dir / run_id)
    if settings.otel_endpoint:
        tracer.enable_otel(settings.otel_endpoint)
    client = client or make_client(settings)
    ctx = RunContext(settings=settings, client=client, tracer=tracer)
    graph = build_graph(ctx)
    log = logging.getLogger("rfp_agent")
    summary_path = ""
    with activate(tracer):
        t0 = time.perf_counter()
        last = t0
        for update in graph.stream(initial_state(input_path), {"recursion_limit": 60},
                                   stream_mode="updates"):
            for node, delta in update.items():
                now = time.perf_counter()
                log.info("[%6.1fs] done %-22s (+%.1fs)%s", now - t0, node, now - last,
                         _describe(delta))
                last = now
                if delta and "summary_path" in delta:
                    summary_path = delta["summary_path"]
    tracer.close()
    return summary_path, tracer


def _describe(delta: dict | None) -> str:
    if not delta:
        return ""
    bits = []
    for key in ("requirements", "approach", "risks"):
        if key in delta:
            bits.append(f"{key}={len(delta[key])}")
    if "pending" in delta and delta["pending"]:
        bits.append(f"next={delta['pending'][0]}")
    return "  " + " ".join(bits) if bits else ""


def print_usage_table(tracer: Tracer) -> None:
    rows = tracer.summary_by_node()
    header = (f"\n{'node':<22} {'llm':>4} {'embed':>5} {'prompt_tok':>10} {'compl_tok':>9} "
              f"{'latency_s':>9} {'retries':>7} {'errors':>6}")
    print(header)
    print("-" * (len(header) - 1))

    def line(name: str, r: dict) -> str:
        return (f"{name:<22} {int(r['calls']):>4} {int(r['embed_calls']):>5} "
                f"{int(r['prompt_tokens']):>10} {int(r['completion_tokens']):>9} "
                f"{r['latency_ms'] / 1000:>9.1f} {int(r['retries']):>7} {int(r['errors']):>6}")

    for node, r in rows.items():
        print(line(node, r))
    print("-" * (len(header) - 1))
    t = tracer.totals()
    print(line("TOTAL", t))
    print(f"cost: ${t['cost_usd']:.4f}  (local models are free; set RFP_PRICE_* for hosted APIs)")


def eval_command(args: argparse.Namespace) -> int:
    from pathlib import Path

    from .config import REPO_ROOT
    from .evals.report import evaluate_runs, write_results

    import json

    from .evals.judge import calibrate

    if args.calibrate:
        print(json.dumps(calibrate(Path(args.calibrate)), indent=2))
        return 0
    stamp = f"{datetime.now():%Y%m%d-%H%M%S}"
    run_dirs = [Path(p) for p in args.runs]
    settings = get_settings(chat_model=args.chat_model)
    for k in range(args.repeat):
        rid = f"eval-{stamp}-{k + 1}"
        logging.getLogger("rfp_agent").warning("=== eval repeat %d/%d: %s", k + 1,
                                               args.repeat, rid)
        run(args.input, run_id=rid, chat_model=args.chat_model)
        run_dirs.append(settings.runs_dir / rid)
    if not run_dirs:
        print("nothing to score: pass run directories or --repeat N")
        return 2
    gold, scores = evaluate_runs(run_dirs, Path(args.gold) if args.gold else None,
                                 REPO_ROOT / "evals" / "gold")
    name = args.name or stamp
    out_dir = REPO_ROOT / "evals" / "results"
    if args.judge:
        _judge_runs(run_dirs, gold, scores, settings, args.judge_model, out_dir, name)
    md, js = write_results(gold, scores, out_dir, name)
    print(md.read_text().split("\n## Per-run detail")[0])
    print(f"results: {md}\n         {js}")
    return 0 if all(s.schema_valid for s in scores) else 1


def _judge_runs(run_dirs, gold, scores, settings, judge_model, out_dir, name) -> None:
    import json

    from .evals.judge import run_judge
    from .schemas import SolutionSummary

    js = settings.model_copy(update={"chat_model": judge_model or settings.judge_model})
    client = make_client(js)
    log = logging.getLogger("rfp_agent")
    lines = []
    for d, s in zip(run_dirs, scores):
        if not s.schema_valid:
            continue
        summary = SolutionSummary.model_validate_json((d / "summary.json").read_text())
        t0 = time.perf_counter()
        judgments, metrics, usage = run_judge(summary, gold, client, js, s.run,
                                              out_dir / f"{name}.judge" / s.run)
        metrics["judge_min"] = round((time.perf_counter() - t0) / 60, 1)
        s.metrics.update(metrics)
        lines += [json.dumps(j.to_json()) for j in judgments]
        log.warning("judged %s with %s: %d judgments in %.1f min", s.run, client.model,
                    len(judgments), metrics["judge_min"])
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.judgments.jsonl").write_text("\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rfp_agent")
    sub = parser.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run", help="analyse an RFP and write runs/<run_id>/summary.{json,md}")
    r.add_argument("--input", default="inputs", help="RFP file (.md/.pdf/.docx) or a directory")
    r.add_argument("--model", dest="chat_model", help="chat model (default from config)")
    r.add_argument("--run-id")
    r.add_argument("--max-revisions", type=int)
    r.add_argument("-q", "--quiet", action="store_true")
    e = sub.add_parser("eval", help="score runs against a gold set -> evals/results/<name>.md")
    e.add_argument("runs", nargs="*", help="run directories to score (e.g. runs/live9)")
    e.add_argument("--gold", help="gold YAML (default: evals/gold/<input stem>.yaml)")
    e.add_argument("--repeat", type=int, default=0,
                   help="first run the pipeline N times on --input, then score those runs")
    e.add_argument("--input", default="inputs/rfp_synthetic_main.md")
    e.add_argument("--model", dest="chat_model")
    e.add_argument("--name", help="results file name (default: timestamp)")
    e.add_argument("--judge", action="store_true",
                   help="also run the local LLM judge (rubric scores, see prompts/judge_*.md)")
    e.add_argument("--judge-model", help="judge model (default: RFP_JUDGE_MODEL / llama3.1:8b)")
    e.add_argument("--calibrate", metavar="JUDGMENTS_JSONL",
                   help="report judge-vs-human agreement for a labelled judgments file")
    e.add_argument("-q", "--quiet", action="store_true")
    c = sub.add_parser("cost", help="token use per run and what it would cost on hosted Claude")
    c.add_argument("runs", nargs="+", help="run directories (e.g. runs/after-main)")
    c.add_argument("--monthly", type=int, default=50, help="RFPs per month for the projection")
    c.add_argument("--out", help="also write the markdown report to this file")
    args = parser.parse_args(argv)

    sys.stdout.reconfigure(line_buffering=True)  # live progress even when piped to a file
    logging.basicConfig(level=logging.WARNING if getattr(args, "quiet", False) else logging.INFO,
                        format="%(message)s", stream=sys.stdout)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    if args.command == "eval":
        return eval_command(args)
    if args.command == "cost":
        from pathlib import Path

        from .costs import render_markdown, run_costs
        md = render_markdown([run_costs(Path(r)) for r in args.runs], args.monthly)
        print(md)
        if args.out:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text(md)
        return 0
    summary_path, tracer = run(args.input, run_id=args.run_id, chat_model=args.chat_model,
                               max_revisions=args.max_revisions)
    print_usage_table(tracer)
    print(f"\nsummary: {summary_path}\n         {summary_path.replace('.json', '.md')}"
          f"\ntrace:   {tracer.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
