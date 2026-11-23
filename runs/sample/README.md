# Sample runs

Full outputs of two real runs, so you can read the results without running anything.
Other runs stay out of git (`runs/*` is ignored).

## `main-final/`: the current pipeline on the main RFP

Run `eval-20261122-204928-1`, made on 2026-11-22 with the final code (including the date check) on a 16 GB M2 Pro. Settings:
- **Models:** `qwen2.5:7b` and `nomic-embed-text`
- **Prompts:** extract 1.4.0, design 2.0.0, risks 1.2.0, critic 1.0.0

| File | Contents |
|---|---|
| `summary.md` | the report for people: requirements with quotes, approach, risks, open questions |
| `summary.json` | the same output in validated JSON (`SolutionSummary`) |
| `trace.jsonl` | one line per model call and agent step: tokens, latency, prompt version, retries |
| `eval.log` | its score against the reviewed gold set (also in `evals/results/datecheck-main.md`) |

**Scores:**
- recall 93% on core requirements, 96% on must requirements
- precision 100%
- 6/6 trap checks
- 3/3 planted risks found and cited
- wall time 14.4 min, with 1 critic revision

**What happened in the run:**
- The first critic pass found one must requirement (COM-11) missing from the approach and sent it back to the architect, which added it.
- The LLM reviewer's notes are kept in `metadata.critic_history`. They are advisory only.

Score it yourself with no model calls:

```bash
python -m rfp_agent eval runs/sample/main-final --name sample-check
```

## `phase1-live2/`: the first complete run (Phase 1, 8 GB M2)

Kept as evidence for the failure log (`notes/phase1_failures.md`, F4–F10). It predates
the later fixes, so it shows known problems:
- 94 requirements (over-extraction)
- a catch-all approach item
- repeated risks

It took 72.8 minutes on an 8 GB laptop, with 2 critic revisions. Prompts: extract 1.1.0, design 1.0.0, risks 1.0.0, critic 1.0.0.
