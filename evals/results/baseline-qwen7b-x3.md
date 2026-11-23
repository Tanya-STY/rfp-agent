# Eval results

Gold: `inputs/rfp_synthetic_main.md` (57 core / 35 optional requirements, 3 planted risks; status: **draft**). Generated 2026-11-21 19:30.

| Metric | eval-20261121-184341-1 | eval-20261121-184341-2 | eval-20261121-184341-3 |
|---|---:|---:|---:|
| Schema valid | yes | yes | yes |
| Requirements extracted | 76 | 76 | 76 |
| Recall: core gold | 84% | 84% | 84% |
| Recall: core gold, must | 83% | 83% | 83% |
| Recall: core, quoted anywhere | 96% | 96% | 96% |
| Precision (matches any gold) | 100% | 100% | 100% |
| Precision, one per obligation | 99% | 99% | 99% |
| False positives | 0 | 0 | 0 |
| Split obligations (extra preds) | 1 | 1 | 1 |
| Priority accuracy (matched core) | 96% | 96% | 96% |
| Grounded quotes | 100% | 100% | 100% |
| Dropped as ungrounded | 0 | 0 | 0 |
| Trap checks passed | 6/7 | 5/7 | 6/7 |
| Planted risks found + cited | 2/3 | 1/3 | 2/3 |
| Expected risks found | 0 | 1 | 1 |
| Approach covers must reqs | 100% | 100% | 100% |
| Judge: requirement faithful | 75% | 75% | 75% |
| Judge: priority reasonable | 75% | 75% | 75% |
| Judge: approach specificity (1-5) | 3.05 | 3.06 | 3.00 |
| Judge: constraint violations | 0 | 0 | 0 |
| Judge: risk specificity (1-5) | 4.60 | 4.00 | 4.00 |
| Judge: mitigation quality (1-5) | 4.40 | 4.75 | 5.00 |
| Judge time (min) | 2.10 | 1.90 | 2.00 |
| Critic passed | yes | yes | yes |
| Revisions | 1 | 1 | 0 |
| Wall time (min) | 15.3 | 14.3 | 11.1 |
| LLM calls | 44 | 44 | 28 |
| Prompt tokens | 56,298 | 54,533 | 37,160 |
| Completion tokens | 22,336 | 21,074 | 16,531 |

## Across runs

| Metric | mean | sd |
|---|---:|---:|
| Requirements extracted | 76.0 | 0.0 |
| Recall: core gold | 84.2% | 0.0% |
| Recall: core gold, must | 82.6% | 0.0% |
| Recall: core, quoted anywhere | 96.5% | 0.0% |
| Precision (matches any gold) | 100.0% | 0.0% |
| Precision, one per obligation | 98.7% | 0.0% |
| False positives | 0.0 | 0.0 |
| Split obligations (extra preds) | 1.0 | 0.0 |
| Priority accuracy (matched core) | 95.8% | 0.0% |
| Grounded quotes | 100.0% | 0.0% |
| Dropped as ungrounded | 0.0 | 0.0 |
| Expected risks found | 0.7 | 0.6 |
| Approach covers must reqs | 100.0% | 0.0% |
| Judge: requirement faithful | 75.0% | 0.0% |
| Judge: priority reasonable | 75.0% | 0.0% |
| Judge: approach specificity (1-5) | 3.0 | 0.0 |
| Judge: constraint violations | 0.0 | 0.0 |
| Judge: risk specificity (1-5) | 4.2 | 0.3 |
| Judge: mitigation quality (1-5) | 4.7 | 0.3 |
| Judge time (min) | 2.0 | 0.1 |
| Critic passed | 1.0 | 0.0 |
| Revisions | 0.7 | 0.6 |
| Wall time (min) | 13.6 | 2.2 |
| LLM calls | 38.7 | 9.2 |
| Prompt tokens | 49330.3 | 10576.7 |
| Completion tokens | 19980.3 | 3053.1 |

Consistency: mean pairwise Jaccard of core items found **1.00**; 48 core items found in every run, 48 in at least one (of 57).

## Per-run detail

### eval-20261121-184341-1

Model `qwen2.5:7b`; prompts: analyze_risks=1.1.0, critic=1.0.0, design_approach=2.0.0, executive_summary=1.0.0, extract_requirements=1.3.0

Trap checks: priority:LANG-ZH ✓, priority:LANG-BM ✓, buried:FR-UI ✓, buried:FR-EXPLAIN ✓, risk:TRAP-TIMELINE ✓, risk:TRAP-RETENTION ✗, risk:TRAP-REALTIME ✓

Missed core (9): COM-RUN, FR-5b, FR-7b, INT-2b, INT-3b, SEC-3a, SEC-4a, SEC-5b, SEC-REG

Wrong priority: FR-9 (FR-21: must, expected should), SEC-SIU (NFR-14: should, expected must)

Split obligations: FR-8a → FR-18, FR-19

### eval-20261121-184341-2

Model `qwen2.5:7b`; prompts: analyze_risks=1.1.0, critic=1.0.0, design_approach=2.0.0, executive_summary=1.0.0, extract_requirements=1.3.0

Trap checks: priority:LANG-ZH ✓, priority:LANG-BM ✓, buried:FR-UI ✓, buried:FR-EXPLAIN ✓, risk:TRAP-TIMELINE ✗, risk:TRAP-RETENTION ✗, risk:TRAP-REALTIME ✓

Missed core (9): COM-RUN, FR-5b, FR-7b, INT-2b, INT-3b, SEC-3a, SEC-4a, SEC-5b, SEC-REG

Wrong priority: FR-9 (FR-21: must, expected should), SEC-SIU (NFR-14: should, expected must)

Split obligations: FR-8a → FR-18, FR-19

### eval-20261121-184341-3

Model `qwen2.5:7b`; prompts: analyze_risks=1.1.0, critic=1.0.0, design_approach=2.0.0, executive_summary=1.0.0, extract_requirements=1.3.0

Trap checks: priority:LANG-ZH ✓, priority:LANG-BM ✓, buried:FR-UI ✓, buried:FR-EXPLAIN ✓, risk:TRAP-TIMELINE ✗, risk:TRAP-RETENTION ✓, risk:TRAP-REALTIME ✓

Missed core (9): COM-RUN, FR-5b, FR-7b, INT-2b, INT-3b, SEC-3a, SEC-4a, SEC-5b, SEC-REG

Wrong priority: FR-9 (FR-21: must, expected should), SEC-SIU (NFR-14: should, expected must)

Split obligations: FR-8a → FR-18, FR-19
