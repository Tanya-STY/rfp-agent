# RFP Analysis Agent

Ingests an RFP brief from `inputs/` and produces a structured solution summary
(requirements, solution approach, risks, open questions) using a multi-agent LangGraph
workflow on a local LLM (Ollama). Every requirement is grounded in a verbatim quote that
is checked by code; a critic loop routes feedback back to the agent responsible.

- **Why it's built this way:** [DECISIONS.md](DECISIONS.md), including the architecture diagram and failure log summary.
- **What it assumes:** [ASSUMPTIONS.md](ASSUMPTIONS.md).
- **The prompts and why:** [PROMPTS.md](PROMPTS.md).
- **Demo script:** [DEMO.md](DEMO.md).
- **Time log:** [TIMELOG.md](TIMELOG.md).
- **Sample output:** [runs/sample/main-final/summary.md](runs/sample/main-final/summary.md) (scored in [evals/results/datecheck-main.md](evals/results/datecheck-main.md)).
- **Demo video (about 5 min):** [watch on Google Drive](https://drive.google.com/file/d/1wF3rRDvgbwYvxeMZcEHbdhiGIwB3ORNd/view?usp=sharing). A captioned walkthrough is also in [demo/demo_walkthrough.pdf](demo/demo_walkthrough.pdf).

## How I used AI tools

The brief allows AI tools, so here is exactly what they did and what I did.

**Building it:** I used **Claude Code** (Anthropic's coding assistant) throughout. It wrote most of the code, prompts, tests and documentation, working from my instructions. It also drafted the three test RFPs and their first gold labels.

**What I did:**
- **Set the direction:** what to build, which trade-offs to accept, and what to fix next (for example, adding the date check after spotting an invented date in the demo).
- **Reviewed the gold labels myself** and changed several (FR-EXPLAIN, LANG-BM, SEC-SIU, SCOPE-7). The labels are what the scores are measured against, so they had to be my judgement, not the AI's.
- **Checked the results** against the RFPs and approved or rejected changes before they were merged.
- **Recorded the demo** and wrote this submission.

**How AI output was checked, rather than trusted:**
- **85 offline tests**, including one for every failure that was fixed.
- **Scores computed in code** against my reviewed labels, so anyone can re-run them (`python -m rfp_agent eval`).
- **Real runs, not just tests.** Every failure in the log (F1–F19 and the phase 2 findings) came from a real run, and each fix was confirmed by re-running.
- **An LLM judge was tried and rejected for headline numbers** because it agreed with my labels only half the time.

**At run time** the pipeline uses no hosted AI: everything runs on local open models through Ollama. Claude prices appear only as a cost comparison.

## Setup (fresh Mac)

Requirements: Python 3.12 and [Ollama](https://ollama.com). Apple Silicon with 16 GB+
RAM recommended; on 8 GB a full run takes ~70 min (see `notes/phase1_failures.md`).

```bash
# 1. Ollama (desktop app + CLI), then start it once so the server runs on :11434
brew install --cask ollama
open -a Ollama            # or: ollama serve
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
ollama list               # both models should be listed

# 2. Python environment (from the repo root)
python3 --version         # 3.12.x (e.g. via pyenv or `brew install python@3.12`)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Offline tests (no Ollama needed)
python -m pytest -q
```

### macOS 13 (Ventura)

The Ollama app needs macOS 14, and the current CLI crashes on Metal under macOS 13.
Use the official v0.11.10 CLI build (minimum macOS 13.0, full GPU use):

```bash
mkdir -p ~/.local/ollama-0.11 && cd ~/.local/ollama-0.11
curl -sSLO https://github.com/ollama/ollama/releases/download/v0.11.10/ollama-darwin.tgz
tar xzf ollama-darwin.tgz && rm ollama-darwin.tgz
OLLAMA_KEEP_ALIVE=30m ./ollama serve      # leave running; pull models from another shell
```

If Homebrew cannot build Python 3.12 (it needs the Xcode Command Line Tools on Ventura),
create the venv from a conda Python instead:
`conda create -p ./.conda-py312 python=3.12 && ./.conda-py312/bin/python -m venv .venv`.

## Run

```bash
python -m rfp_agent run --input inputs/rfp_synthetic_main.md
# options: --model <ollama model>  --run-id <id>  --max-revisions <n>  -q
```

Outputs go to `runs/<run_id>/`:

| File | Contents |
|---|---|
| `summary.json` | validated `SolutionSummary` (requirements, approach, risks, assumptions, open questions, metadata) |
| `summary.md` | the same, formatted for humans |
| `trace.jsonl` | one line per LLM/embedding call (node, prompt version, tokens, latency, retries, errors) and per node span |

Configuration is in `rfp_agent/config.py`; every field can be overridden with an
`RFP_`-prefixed environment variable, e.g. `RFP_CHAT_MODEL=llama3.1:8b`,
`RFP_MAX_REVISIONS=1`, `RFP_PROVIDER=openai_compat RFP_BASE_URL=http://localhost:8000`.

## Evaluate

```bash
python -m rfp_agent eval runs/sample/main-final            # score an existing run (no model calls)
python -m rfp_agent eval --repeat 3 --name baseline-qwen7b  # run 3x, then score (consistency)
```

Runs are scored against a hand-labelled gold set, `evals/gold/<input stem>.yaml`
(requirements as verbatim quotes, plus planted traps and risks). Matching is
deterministic: a predicted requirement matches a gold one when their quotes overlap in
the RFP text. Results go to `evals/results/<name>.{md,json}`. The metric definitions
are in the `rfp_agent/evals/scoring.py` docstring.

**LLM judge (optional, local):** `--judge` adds rubric scores the matcher cannot see:
whether requirement descriptions are faithful to their quotes, approach specificity and
hard-constraint violations, and risk and mitigation quality. It runs one small judgment
per item on a different model family from the pipeline (`ollama pull llama3.1:8b`;
override with `--judge-model` or `RFP_JUDGE_MODEL`). Every judgment is written to
`evals/results/<name>.judgments.jsonl` with an empty `human` field. Fill in some, e.g.
`"human": {"faithful": true}`, then run
`python -m rfp_agent eval --calibrate evals/results/<name>.judgments.jsonl`
to see how often the judge agrees with a person.

## Dashboard

```bash
streamlit run app/dashboard.py      # http://localhost:8501
```

Four tabs:
- **Run:** analyse an RFP from `inputs/`, `evals/rfps/` or an upload.
- **Results:** requirements with quotes, approach, risks, open questions.
- **Observability:** time and tokens per agent, a run timeline, and the hosted-cost estimate.
- **Evaluation:** any `evals/results/*.json`.

It only reads the files the CLI writes, so it shows past runs without re-running them.

## Observability and cost

Every model call and graph node is written to `runs/<id>/trace.jsonl`. This file is the source of truth for the dashboard, the evals and the cost report.

```bash
python -m rfp_agent cost runs/sample/main-final --out evals/results/cost.md
```

The cost report shows token use per run and per agent: $0 locally, and what the same volume would cost on Claude Haiku, Sonnet or Opus 5.5. These are estimates: the token counts come from the local tokenizer.

**Phoenix (optional):** the same trace can be mirrored to Arize Phoenix over OpenTelemetry. Phoenix is installed in its own venv because it has many dependencies.

```bash
python -m venv .phoenix-venv && .phoenix-venv/bin/pip install arize-phoenix
.phoenix-venv/bin/phoenix serve                      # UI on http://localhost:6006
RFP_OTEL_ENDPOINT=http://localhost:6006/v1/traces python -m rfp_agent run --input ...
```

Each run appears as one trace, with a span per agent and a child span per model call. Each model-call span carries its tokens, latency and prompt version. If Phoenix isn't running, the run still completes; only a warning is logged.

## Tests

Tests are fully offline: the graph test runs the whole workflow (including a critic
revision loop) against a scripted `FakeLLMClient` in about a second.

## Layout

```
inputs/              RFP briefs (.md / .pdf / .docx)
app/dashboard.py     Streamlit dashboard
prompts/             one versioned prompt per agent (YAML front-matter + Jinja2)
rfp_agent/
  config.py          settings (env-overridable)
  schemas.py         Pydantic models: domain output + smaller LLM output shapes
  ingest.py          load md/pdf/docx, normalise, split into sections/chunks
  retrieval.py       numpy vector index (nomic-embed-text) + quote_in_source grounding check
  llm.py             LLMClient protocol, OllamaClient (structured output + retries), OpenAI-compatible stub
  tracing.py         record_call hook + node spans -> runs/<id>/trace.jsonl
  otel.py            optional OpenTelemetry export of the same spans (Phoenix)
  costs.py           cost report: local $0 vs hosted-model estimate
  guard.py           prompt-injection quarantine at ingest
  prompts.py         prompt loader (prompts explained in PROMPTS.md)
  agents/            extractor, architect (bounded search tool loop), risk_analyst, critic
  graph.py           LangGraph wiring + critic routing
  report.py          final assembly, summary.json / summary.md
  cli.py             `python -m rfp_agent run|eval|cost ...`
  evals/             eval harness: gold loading, quote-span matching, metrics, report
tests/               pytest suite (offline)
evals/gold/          hand-labelled gold sets (one YAML per input)
evals/results/       scored results tables
evals/rfps/          held-out test RFPs (water utility, adversarial council)
evals/review/        local review app for labelling judge verdicts and gold sets
notes/               working notes (live-run failure log)
runs/sample/         two full runs: main-final (current pipeline) and phase1-live2 (evidence)
```
