# Eval results

Gold: `inputs/rfp_synthetic_main.md` (57 core / 35 optional requirements, 3 planted risks; status: **draft**). Generated 2026-11-22 00:08.

| Metric | eval-20261121-233403-1 | eval-20261121-233403-2 |
|---|---:|---:|
| Schema valid | yes | yes |
| Requirements extracted | 82 | 82 |
| Recall: core gold | 93% | 93% |
| Recall: core gold, must | 96% | 96% |
| Recall: core, quoted anywhere | 93% | 93% |
| Precision (matches any gold) | 100% | 100% |
| Precision, one per obligation | 98% | 98% |
| False positives | 0 | 0 |
| Split obligations (extra preds) | 2 | 2 |
| Priority accuracy (matched core) | 96% | 96% |
| Grounded quotes | 100% | 100% |
| Dropped as ungrounded | 0 | 0 |
| Trap checks passed | 7/7 | 7/7 |
| Planted risks found + cited | 3/3 | 3/3 |
| Expected risks found | 0 | 1 |
| Approach covers must reqs | 100% | 100% |
| Critic passed | yes | yes |
| Revisions | 2 | 0 |
| Wall time (min) | 21.8 | 12.9 |
| LLM calls | 66 | 31 |
| Prompt tokens | 83,464 | 43,388 |
| Completion tokens | 27,295 | 16,275 |

## Across runs

| Metric | mean | sd |
|---|---:|---:|
| Requirements extracted | 82.0 | 0.0 |
| Recall: core gold | 93.0% | 0.0% |
| Recall: core gold, must | 95.7% | 0.0% |
| Recall: core, quoted anywhere | 93.0% | 0.0% |
| Precision (matches any gold) | 100.0% | 0.0% |
| Precision, one per obligation | 97.6% | 0.0% |
| False positives | 0.0 | 0.0 |
| Split obligations (extra preds) | 2.0 | 0.0 |
| Priority accuracy (matched core) | 96.2% | 0.0% |
| Grounded quotes | 100.0% | 0.0% |
| Dropped as ungrounded | 0.0 | 0.0 |
| Expected risks found | 0.5 | 0.7 |
| Approach covers must reqs | 100.0% | 0.0% |
| Critic passed | 1.0 | 0.0 |
| Revisions | 1.0 | 1.4 |
| Wall time (min) | 17.4 | 6.3 |
| LLM calls | 48.5 | 24.7 |
| Prompt tokens | 63426.0 | 28338.0 |
| Completion tokens | 21785.0 | 7792.3 |

Consistency: mean pairwise Jaccard of core items found **1.00**; 53 core items found in every run, 53 in at least one (of 57).

## Per-run detail

### eval-20261121-233403-1

Model `qwen2.5:7b`; prompts: analyze_risks=1.2.0, critic=1.0.0, design_approach=2.0.0, executive_summary=1.0.0, extract_requirements=1.4.0

Trap checks: priority:LANG-ZH ✓, priority:LANG-BM ✓, buried:FR-UI ✓, buried:FR-EXPLAIN ✓, risk:TRAP-TIMELINE ✓, risk:TRAP-RETENTION ✓, risk:TRAP-REALTIME ✓

Missed core (4): COM-RUN, INT-1c, INT-3b, SEC-REG

Wrong priority: FR-9 (FR-23: must, expected should), SEC-SIU (NFR-13: should, expected must)

Split obligations: FR-8a → FR-20, FR-21; INT-SFTP → INT-07, INT-08

### eval-20261121-233403-2

Model `qwen2.5:7b`; prompts: analyze_risks=1.2.0, critic=1.0.0, design_approach=2.0.0, executive_summary=1.0.0, extract_requirements=1.4.0

Trap checks: priority:LANG-ZH ✓, priority:LANG-BM ✓, buried:FR-UI ✓, buried:FR-EXPLAIN ✓, risk:TRAP-TIMELINE ✓, risk:TRAP-RETENTION ✓, risk:TRAP-REALTIME ✓

Missed core (4): COM-RUN, INT-1c, INT-3b, SEC-REG

Wrong priority: FR-9 (FR-23: must, expected should), SEC-SIU (NFR-13: should, expected must)

Split obligations: FR-8a → FR-20, FR-21; INT-SFTP → INT-07, INT-08
