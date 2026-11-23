# Eval results

Gold: `inputs/rfp_synthetic_main.md` (57 core / 35 optional requirements, 3 planted risks; status: **draft**). Generated 2026-11-21 20:16.

| Metric | eval-20261121-184341-1 | after-main |
|---|---:|---:|
| Schema valid | yes | yes |
| Requirements extracted | 76 | 81 |
| Recall: core gold | 84% | 93% |
| Recall: core gold, must | 83% | 96% |
| Recall: core, quoted anywhere | 96% | 93% |
| Precision (matches any gold) | 100% | 100% |
| Precision, one per obligation | 99% | 98% |
| False positives | 0 | 0 |
| Split obligations (extra preds) | 1 | 2 |
| Priority accuracy (matched core) | 96% | 94% |
| Grounded quotes | 100% | 100% |
| Dropped as ungrounded | 0 | 0 |
| Trap checks passed | 6/7 | 6/7 |
| Planted risks found + cited | 2/3 | 2/3 |
| Expected risks found | 0 | 1 |
| Approach covers must reqs | 100% | 100% |
| Judge: requirement faithful | 75% | 75% |
| Judge: priority reasonable | 75% | 100% |
| Judge: approach specificity (1-5) | 3.05 | 3.00 |
| Judge: constraint violations | 0 | 0 |
| Judge: risk specificity (1-5) | 4.60 | 3.86 |
| Judge: mitigation quality (1-5) | 4.40 | 4.43 |
| Judge time (min) | 2.10 | 2.00 |
| Critic passed | yes | yes |
| Revisions | 1 | 1 |
| Wall time (min) | 15.3 | 14.0 |
| LLM calls | 44 | 48 |
| Prompt tokens | 56,298 | 60,186 |
| Completion tokens | 22,336 | 20,606 |

## Across runs

| Metric | mean | sd |
|---|---:|---:|
| Requirements extracted | 78.5 | 3.5 |
| Recall: core gold | 88.6% | 6.2% |
| Recall: core gold, must | 89.1% | 9.3% |
| Recall: core, quoted anywhere | 94.8% | 2.5% |
| Precision (matches any gold) | 100.0% | 0.0% |
| Precision, one per obligation | 98.1% | 0.8% |
| False positives | 0.0 | 0.0 |
| Split obligations (extra preds) | 1.5 | 0.7 |
| Priority accuracy (matched core) | 95.0% | 1.1% |
| Grounded quotes | 100.0% | 0.0% |
| Dropped as ungrounded | 0.0 | 0.0 |
| Expected risks found | 0.5 | 0.7 |
| Approach covers must reqs | 100.0% | 0.0% |
| Judge: requirement faithful | 75.0% | 0.0% |
| Judge: priority reasonable | 87.5% | 17.7% |
| Judge: approach specificity (1-5) | 3.0 | 0.0 |
| Judge: constraint violations | 0.0 | 0.0 |
| Judge: risk specificity (1-5) | 4.2 | 0.5 |
| Judge: mitigation quality (1-5) | 4.4 | 0.0 |
| Judge time (min) | 2.0 | 0.1 |
| Critic passed | 1.0 | 0.0 |
| Revisions | 1.0 | 0.0 |
| Wall time (min) | 14.7 | 0.9 |
| LLM calls | 46.0 | 2.8 |
| Prompt tokens | 58242.0 | 2749.2 |
| Completion tokens | 21471.0 | 1223.3 |

Consistency: mean pairwise Jaccard of core items found **0.87**; 47 core items found in every run, 54 in at least one (of 57).

## Per-run detail

### eval-20261121-184341-1

Model `qwen2.5:7b`; prompts: analyze_risks=1.1.0, critic=1.0.0, design_approach=2.0.0, executive_summary=1.0.0, extract_requirements=1.3.0

Trap checks: priority:LANG-ZH ✓, priority:LANG-BM ✓, buried:FR-UI ✓, buried:FR-EXPLAIN ✓, risk:TRAP-TIMELINE ✓, risk:TRAP-RETENTION ✗, risk:TRAP-REALTIME ✓

Missed core (9): COM-RUN, FR-5b, FR-7b, INT-2b, INT-3b, SEC-3a, SEC-4a, SEC-5b, SEC-REG

Wrong priority: FR-9 (FR-21: must, expected should), SEC-SIU (NFR-14: should, expected must)

Split obligations: FR-8a → FR-18, FR-19

### after-main

Model `qwen2.5:7b`; prompts: analyze_risks=1.1.0, critic=1.0.0, design_approach=2.0.0, executive_summary=1.0.0, extract_requirements=1.4.0

Trap checks: priority:LANG-ZH ✓, priority:LANG-BM ✓, buried:FR-UI ✓, buried:FR-EXPLAIN ✓, risk:TRAP-TIMELINE ✓, risk:TRAP-RETENTION ✗, risk:TRAP-REALTIME ✓

Missed core (4): COM-RUN, INT-1c, INT-3b, SEC-REG

Wrong priority: FR-9 (FR-23: must, expected should), SEC-SIU (NFR-13: should, expected must), TEAM-MY (SEC-12: should, expected must)

Split obligations: FR-8a → FR-20, FR-21; INT-SFTP → INT-07, INT-08
