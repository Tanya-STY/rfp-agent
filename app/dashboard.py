"""RFP agent dashboard: run the pipeline, read the result, see the metrics and evals.

    streamlit run app/dashboard.py

Reads only files the CLI writes (runs/<id>/summary.json, trace.jsonl, evals/results/*.json),
so it shows past runs without re-running anything, and the CLI stays the single way the
pipeline is executed (the Run tab just calls it).
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from rfp_agent.costs import HOSTED_PRICES, TOKENIZER_NOTE, run_costs  # noqa: E402

RUNS = ROOT / "runs"
RESULTS = ROOT / "evals" / "results"
INPUT_DIRS = [ROOT / "inputs", ROOT / "evals" / "rfps"]
PRIORITY_ORDER = ["must", "should", "could"]

st.set_page_config(page_title="RFP Agent", page_icon="📑", layout="wide")


# ----------------------------------------------------------------------------- loaders

@st.cache_data(ttl=10)
def list_runs() -> list[str]:
    dirs = [d for d in RUNS.iterdir() if (d / "summary.json").exists()]
    return [d.name for d in sorted(dirs, key=lambda d: (d / "summary.json").stat().st_mtime,
                                   reverse=True)]


@st.cache_data
def load_summary(run: str, mtime: float) -> dict:
    return json.loads((RUNS / run / "summary.json").read_text())


@st.cache_data
def load_trace(run: str, mtime: float) -> list[dict]:
    path = RUNS / run / "trace.jsonl"
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()] if path.exists() else []


def mtime(run: str) -> float:
    return (RUNS / run / "summary.json").stat().st_mtime


def pick_run(key: str) -> str | None:
    runs = list_runs()
    if not runs:
        st.info("No runs yet. Use the **Run** tab or `python -m rfp_agent run`.")
        return None
    default = st.session_state.get("last_run")
    idx = runs.index(default) if default in runs else 0
    return st.selectbox("Run", runs, index=idx, key=key,
                        format_func=lambda r: f"{r}  ·  {load_summary(r, mtime(r))['metadata']['input_file']}")


# ------------------------------------------------------------------------------- tabs

st.title("RFP Agent")
st.caption("Local multi-agent RFP analysis: requirements → approach → risks, with a critic loop. "
           "Every requirement is grounded in a verbatim quote from the RFP.")
t_run, t_result, t_obs, t_eval = st.tabs(["▶ Run", "📄 Results", "📈 Observability", "🎯 Evaluation"])

# ---- Run ------------------------------------------------------------------------------
with t_run:
    files = [p for d in INPUT_DIRS if d.exists() for p in sorted(d.iterdir())
             if p.suffix.lower() in {".md", ".pdf", ".docx"}]
    c1, c2 = st.columns([2, 1])
    choice = c1.selectbox("RFP", files, format_func=lambda p: str(p.relative_to(ROOT)))
    upload = c2.file_uploader("…or upload one", type=["md", "pdf", "docx"])
    st.caption("Runs on local Ollama (qwen2.5:7b). On an M2 Pro: ~2.5 min for the council RFQ, "
               "~4.5 min for the water RFP, ~14 min for the main RFP.")
    if st.button("Analyse RFP", type="primary"):
        if upload is not None:
            dest = ROOT / "inputs" / "uploads" / upload.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(upload.getvalue())
            choice = dest
        run_id = f"dash-{datetime.now():%Y%m%d-%H%M%S}"
        cmd = [sys.executable, "-m", "rfp_agent", "run", "--input", str(choice), "--run-id", run_id]
        with st.status(f"Running {run_id}…", expanded=True) as status:
            proc = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True)
            log_box, lines = st.empty(), []
            for line in proc.stdout:  # type: ignore[union-attr]
                lines.append(line.rstrip())
                log_box.code("\n".join(lines[-25:]))
            ok = proc.wait() == 0
            status.update(label=f"{run_id} {'finished' if ok else 'failed'}",
                          state="complete" if ok else "error")
        if ok:
            st.session_state["last_run"] = run_id
            list_runs.clear()
            st.success("Done. Open the **Results** tab.")

# ---- Results --------------------------------------------------------------------------
with t_result:
    run = pick_run("run_result")
    if run:
        s = load_summary(run, mtime(run))
        m = s["metadata"]
        reqs = pd.DataFrame(s["requirements"])
        wall = (datetime.fromisoformat(m["finished_at"].rstrip("Z"))
                - datetime.fromisoformat(m["started_at"].rstrip("Z"))).total_seconds() / 60
        k = st.columns(6)
        k[0].metric("Requirements", len(reqs))
        k[1].metric("Must", int((reqs.priority == "must").sum()) if len(reqs) else 0)
        k[2].metric("Approach items", len(s["approach"]))
        k[3].metric("Risks", len(s["risks"]))
        k[4].metric("Critic passed", "yes" if m.get("critic_passed") else "no",
                    f"{m.get('revisions', 0)} revision(s)", delta_color="off")
        k[5].metric("Minutes", f"{wall:.1f}")
        st.markdown(f"**Executive summary.** {s['executive_summary']}")

        for w in m.get("warnings", []):
            st.warning(w)

        st.subheader("Requirements")
        f1, f2, f3 = st.columns([1, 2, 2])
        pri = f1.multiselect("Priority", PRIORITY_ORDER, default=PRIORITY_ORDER)
        cats = sorted(reqs.category.unique()) if len(reqs) else []
        cat = f2.multiselect("Category", cats, default=cats)
        q = f3.text_input("Search", "")
        view = reqs[reqs.priority.isin(pri) & reqs.category.isin(cat)] if len(reqs) else reqs
        if q:
            view = view[view.apply(lambda r: q.lower() in f"{r.title} {r.description} {r.source_quote}".lower(), axis=1)]
        st.dataframe(view[["id", "priority", "category", "title", "description", "source_quote",
                           "source_section", "confidence"]], hide_index=True, use_container_width=True,
                     column_config={"source_quote": st.column_config.TextColumn("Quote (verbatim)", width="large"),
                                    "confidence": st.column_config.ProgressColumn(min_value=0, max_value=1)})

        st.subheader("Approach")
        for i, a in enumerate(s["approach"], 1):
            with st.expander(f"A{i}. {a['summary'][:110]}"):
                st.write(a["summary"])
                st.markdown("**Components:** " + ", ".join(a.get("components", [])))
                st.markdown(f"**Rationale:** {a.get('rationale', '')}")
                st.caption("Covers: " + ", ".join(a["requirement_ids"]))

        st.subheader("Risks")
        if s["risks"]:
            rk = pd.DataFrame(s["risks"])
            rk["linked"] = rk.related_requirement_ids.apply(", ".join)
            st.dataframe(rk[["id", "category", "likelihood", "impact", "title", "description",
                             "mitigation", "linked"]], hide_index=True, use_container_width=True)
        st.subheader("Open questions for the client")
        for oq in s["open_questions"]:
            st.markdown(f"- **{oq['question']}** <small>({oq.get('raised_by', '')}) {oq.get('reason', '')}</small>",
                        unsafe_allow_html=True)
        st.download_button("Download summary (Markdown)", (RUNS / run / "summary.md").read_text(),
                           file_name=f"{run}.md")

# ---- Observability -------------------------------------------------------------------
with t_obs:
    run = pick_run("run_obs")
    if run:
        trace = load_trace(run, mtime(run))
        calls = pd.DataFrame([t for t in trace if t.get("type") == "llm_call"])
        if calls.empty:
            st.info("This run has no trace.")
        else:
            chat = calls[calls.kind == "chat"]
            k = st.columns(5)
            k[0].metric("LLM calls", len(chat))
            k[1].metric("Input tokens", f"{int(chat.prompt_tokens.sum()):,}")
            k[2].metric("Output tokens", f"{int(chat.completion_tokens.sum()):,}")
            k[3].metric("Retries", int(calls.retries.sum()))
            k[4].metric("Errors", int((~calls.success).sum()))

            st.subheader("Where the time and tokens go")
            by = chat.groupby("node").agg(calls=("node", "size"), input=("prompt_tokens", "sum"),
                                          output=("completion_tokens", "sum"),
                                          seconds=("latency_ms", lambda x: x.sum() / 1000)).reset_index()
            c1, c2 = st.columns(2)
            c1.altair_chart(alt.Chart(by).mark_bar().encode(
                x=alt.X("seconds:Q", title="model time (s)"), y=alt.Y("node:N", sort="-x", title=None),
                tooltip=["node", "calls", "seconds"]).properties(height=220), use_container_width=True)
            tok = by.melt(id_vars="node", value_vars=["input", "output"], var_name="tokens", value_name="n")
            c2.altair_chart(alt.Chart(tok).mark_bar().encode(
                x=alt.X("n:Q", title="tokens"), y=alt.Y("node:N", sort="-x", title=None),
                color=alt.Color("tokens:N", scale=alt.Scale(range=["#4C78A8", "#F58518"])),
                tooltip=["node", "tokens", "n"]).properties(height=220), use_container_width=True)

            st.subheader("Timeline")
            ends = [t for t in trace if t.get("type") == "span_end"]
            if ends:
                tl = pd.DataFrame(ends)
                tl["end"] = pd.to_datetime(tl.ts)
                tl["start"] = tl.end - pd.to_timedelta(tl.duration_ms, unit="ms")
                st.altair_chart(alt.Chart(tl).mark_bar().encode(
                    x=alt.X("start:T", title=None), x2="end:T", y=alt.Y("node:N", sort=None, title=None),
                    color=alt.condition(alt.datum.status == "ok", alt.value("#4C78A8"), alt.value("#E45756")),
                    tooltip=["node", "duration_ms", "status"]).properties(height=240),
                    use_container_width=True)
                st.caption("Repeated bars are the critic sending work back for revision.")

            st.subheader("Cost")
            cost = run_costs(RUNS / run)
            cc = st.columns(len(HOSTED_PRICES) + 1)
            cc[0].metric("This run, local", "$0.00")
            for col, (model, usd) in zip(cc[1:], cost["hosted"].items()):
                col.metric(f"If run on {model}", f"${usd:.3f}", f"${usd * 50:.2f} at 50 RFPs/month",
                           delta_color="off")
            st.caption(TOKENIZER_NOTE)

            with st.expander("All LLM calls"):
                st.dataframe(calls[["node", "kind", "model", "prompt_version", "prompt_tokens",
                                    "completion_tokens", "latency_ms", "retries", "success"]],
                             hide_index=True, use_container_width=True)

# ---- Evaluation ----------------------------------------------------------------------
with t_eval:
    files = sorted(RESULTS.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    files = [f for f in files if not f.name.endswith(".judgments.json")]
    if not files:
        st.info("No eval results yet: `python -m rfp_agent eval --repeat 3`.")
    else:
        f = st.selectbox("Results file", files, format_func=lambda p: p.stem)
        d = json.loads(f.read_text())
        st.caption(f"Gold set: `{d['gold']}` (status: {d['gold_status']}). Scoring is deterministic: "
                   "predictions match gold by where their verbatim quotes sit in the RFP.")
        def versions(v) -> dict:  # stored as "node=1.2.0, node=..." in results files
            if isinstance(v, dict):
                return v
            return dict(x.strip().split("=", 1) for x in (v or "").split(",") if "=" in x)

        rows = []
        for r in d["runs"]:
            mt = r["metrics"]
            rows.append({"run": r["run"], "recall (core)": mt.get("recall_core"),
                         "recall (must)": mt.get("recall_must"), "precision": mt.get("precision"),
                         "priority acc": mt.get("priority_acc"), "grounding": mt.get("grounding_rate"),
                         "traps": f"{mt.get('trap_checks_passed')}/{mt.get('trap_checks_total')}",
                         "requirements": mt.get("requirements"), "minutes": mt.get("wall_min"),
                         "extract prompt": versions(mt.get("prompt_versions")).get("extract_requirements"),
                         "risk prompt": versions(mt.get("prompt_versions")).get("analyze_risks")})
        df = pd.DataFrame(rows)
        pct = {c: st.column_config.NumberColumn(format="percent") for c in
               ["recall (core)", "recall (must)", "precision", "priority acc", "grounding"]}
        st.dataframe(df, hide_index=True, use_container_width=True, column_config=pct)
        if d.get("consistency"):
            c = d["consistency"]
            st.markdown(f"**Consistency across runs:** mean pairwise Jaccard of core items found "
                        f"**{c.get('mean_pairwise_jaccard', '–')}** ({c.get('core_found_in_all_runs')} core items found in every run, {c.get('core_found_in_any_run')} in at least one).")
        r = st.selectbox("Details for run", [x["run"] for x in d["runs"]])
        det = next(x for x in d["runs"] if x["run"] == r)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Trap checks**")
            st.dataframe(pd.DataFrame([{"check": k, "passed": "✅" if v.get("passed") else "❌"}
                                       for k, v in (det.get("traps") or {}).items()]),
                         hide_index=True, use_container_width=True)
        with c2:
            st.markdown("**Core requirements missed** (gold ids)")
            st.write(", ".join(det.get("missed_core") or []) or "none")
            st.markdown("**False positives** (extracted, but not in the gold set)")
            fps = det.get("false_positives") or []
            if fps and isinstance(fps[0], dict):
                st.dataframe(pd.DataFrame(fps), hide_index=True, use_container_width=True)
            else:
                st.write(", ".join(map(str, fps)) or "none")
        md = f.with_suffix(".md")
        if md.exists():
            with st.expander("Full results table"):
                st.markdown(md.read_text())
