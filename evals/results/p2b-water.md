# Eval results

Gold: `evals/rfps/rfp_water_fieldops.md` (26 core / 5 optional requirements, 3 planted risks; status: **draft**). Generated 2026-11-21 23:01.

| Metric | eval-20261121-225148-1 | eval-20261121-225148-2 |
|---|---:|---:|
| Schema valid | yes | yes |
| Requirements extracted | 30 | 30 |
| Recall: core gold | 100% | 100% |
| Recall: core gold, must | 100% | 100% |
| Recall: core, quoted anywhere | 100% | 100% |
| Precision (matches any gold) | 100% | 100% |
| Precision, one per obligation | 93% | 93% |
| False positives | 0 | 0 |
| Split obligations (extra preds) | 2 | 2 |
| Priority accuracy (matched core) | 100% | 100% |
| Grounded quotes | 100% | 100% |
| Dropped as ungrounded | 0 | 0 |
| Trap checks passed | 7/7 | 7/7 |
| Planted risks found + cited | 3/3 | 3/3 |
| Expected risks found | 0 | 0 |
| Approach covers must reqs | 100% | 100% |
| Critic passed | yes | yes |
| Revisions | 0 | 0 |
| Wall time (min) | 5.10 | 4.90 |
| LLM calls | 14 | 13 |
| Prompt tokens | 17,909 | 16,574 |
| Completion tokens | 6,313 | 6,346 |

## Across runs

| Metric | mean | sd |
|---|---:|---:|
| Requirements extracted | 30.0 | 0.0 |
| Recall: core gold | 100.0% | 0.0% |
| Recall: core gold, must | 100.0% | 0.0% |
| Recall: core, quoted anywhere | 100.0% | 0.0% |
| Precision (matches any gold) | 100.0% | 0.0% |
| Precision, one per obligation | 93.3% | 0.0% |
| False positives | 0.0 | 0.0 |
| Split obligations (extra preds) | 2.0 | 0.0 |
| Priority accuracy (matched core) | 100.0% | 0.0% |
| Grounded quotes | 100.0% | 0.0% |
| Dropped as ungrounded | 0.0 | 0.0 |
| Expected risks found | 0.0 | 0.0 |
| Approach covers must reqs | 100.0% | 0.0% |
| Critic passed | 1.0 | 0.0 |
| Revisions | 0.0 | 0.0 |
| Wall time (min) | 5.0 | 0.1 |
| LLM calls | 13.5 | 0.7 |
| Prompt tokens | 17241.5 | 944.0 |
| Completion tokens | 6329.5 | 23.3 |

Consistency: mean pairwise Jaccard of core items found **1.00**; 26 core items found in every run, 26 in at least one (of 26).

## Per-run detail

### eval-20261121-225148-1

Model `qwen2.5:7b`; prompts: analyze_risks=1.2.0, critic=1.0.0, design_approach=2.0.0, executive_summary=1.0.0, extract_requirements=1.4.0

Trap checks: priority:GIS ✓, priority:TL-PILOT ✓, buried:OFFLINE ✓, buried:VOICE ✓, risk:TRAP-UNION-TIMELINE ✓, risk:TRAP-VOICE-RECORDS ✓, risk:TRAP-RESPONSE-TIME ✓

Missed core (0): none

Split obligations: S1 → SEC-01, SEC-02; SCOPE-QA → FR-01, FR-02

### eval-20261121-225148-2

Model `qwen2.5:7b`; prompts: analyze_risks=1.2.0, critic=1.0.0, design_approach=2.0.0, executive_summary=1.0.0, extract_requirements=1.4.0

Trap checks: priority:GIS ✓, priority:TL-PILOT ✓, buried:OFFLINE ✓, buried:VOICE ✓, risk:TRAP-UNION-TIMELINE ✓, risk:TRAP-VOICE-RECORDS ✓, risk:TRAP-RESPONSE-TIME ✓

Missed core (0): none

Split obligations: S1 → SEC-01, SEC-02; SCOPE-QA → FR-01, FR-02
