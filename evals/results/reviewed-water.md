# Eval results

Gold: `evals/rfps/rfp_water_fieldops.md` (26 core / 5 optional requirements, 3 planted risks; status: **reviewed**). Generated 2026-11-22 19:05.

| Metric | eval-20261122-000939-1 |
|---|---:|
| Schema valid | yes |
| Requirements extracted | 30 |
| Recall: core gold | 100% |
| Recall: core gold, must | 100% |
| Recall: core, quoted anywhere | 100% |
| Precision (matches any gold) | 100% |
| Precision, one per obligation | 93% |
| False positives | 0 |
| Split obligations (extra preds) | 2 |
| Priority accuracy (matched core) | 100% |
| Grounded quotes | 100% |
| Dropped as ungrounded | 0 |
| Trap checks passed | 7/7 |
| Planted risks found + cited | 3/3 |
| Expected risks found | 1 |
| Approach covers must reqs | 100% |
| Critic passed | yes |
| Revisions | 0 |
| Wall time (min) | 4.50 |
| LLM calls | 14 |
| Prompt tokens | 17,936 |
| Completion tokens | 6,166 |

## Per-run detail

### eval-20261122-000939-1

Model `qwen2.5:7b`; prompts: analyze_risks=1.2.0, critic=1.0.0, design_approach=2.0.0, executive_summary=1.0.0, extract_requirements=1.4.0

Trap checks: priority:GIS ✓, priority:TL-PILOT ✓, buried:OFFLINE ✓, buried:VOICE ✓, risk:TRAP-UNION-TIMELINE ✓, risk:TRAP-VOICE-RECORDS ✓, risk:TRAP-RESPONSE-TIME ✓

Missed core (0): none

Split obligations: S1 → SEC-01, SEC-02; SCOPE-QA → FR-01, FR-02
