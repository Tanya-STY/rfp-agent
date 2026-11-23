# Eval results

Gold: `inputs/rfp_synthetic_main.md` (57 core / 35 optional requirements, 3 planted risks; status: **draft**). Generated 2026-11-21 23:22.

| Metric | eval-20261121-230151-1 | eval-20261121-230151-2 |
|---|---:|---:|
| Schema valid | yes | yes |
| Requirements extracted | 81 | 81 |
| Recall: core gold | 91% | 91% |
| Recall: core gold, must | 94% | 94% |
| Recall: core, quoted anywhere | 91% | 91% |
| Precision (matches any gold) | 100% | 100% |
| Precision, one per obligation | 98% | 98% |
| False positives | 0 | 0 |
| Split obligations (extra preds) | 2 | 2 |
| Priority accuracy (matched core) | 96% | 96% |
| Grounded quotes | 100% | 100% |
| Dropped as ungrounded | 0 | 0 |
| Trap checks passed | 5/7 | 5/7 |
| Planted risks found + cited | 1/3 | 1/3 |
| Expected risks found | 0 | 1 |
| Approach covers must reqs | 100% | 100% |
| Critic passed | yes | yes |
| Revisions | 0 | 0 |
| Wall time (min) | 10.2 | 10.7 |
| LLM calls | 28 | 30 |
| Prompt tokens | 39,172 | 41,896 |
| Completion tokens | 15,096 | 15,745 |

## Across runs

| Metric | mean | sd |
|---|---:|---:|
| Requirements extracted | 81.0 | 0.0 |
| Recall: core gold | 91.2% | 0.0% |
| Recall: core gold, must | 93.5% | 0.0% |
| Recall: core, quoted anywhere | 91.2% | 0.0% |
| Precision (matches any gold) | 100.0% | 0.0% |
| Precision, one per obligation | 97.5% | 0.0% |
| False positives | 0.0 | 0.0 |
| Split obligations (extra preds) | 2.0 | 0.0 |
| Priority accuracy (matched core) | 96.2% | 0.0% |
| Grounded quotes | 100.0% | 0.0% |
| Dropped as ungrounded | 0.0 | 0.0 |
| Expected risks found | 0.5 | 0.7 |
| Approach covers must reqs | 100.0% | 0.0% |
| Critic passed | 1.0 | 0.0 |
| Revisions | 0.0 | 0.0 |
| Wall time (min) | 10.4 | 0.4 |
| LLM calls | 29.0 | 1.4 |
| Prompt tokens | 40534.0 | 1926.2 |
| Completion tokens | 15420.5 | 458.9 |

Consistency: mean pairwise Jaccard of core items found **1.00**; 52 core items found in every run, 52 in at least one (of 57).

## Per-run detail

### eval-20261121-230151-1

Model `qwen2.5:7b`; prompts: analyze_risks=1.2.0, critic=1.0.0, design_approach=2.0.0, executive_summary=1.0.0, extract_requirements=1.4.0

Trap checks: priority:LANG-ZH ✓, priority:LANG-BM ✓, buried:FR-UI ✓, buried:FR-EXPLAIN ✓, risk:TRAP-TIMELINE ✗, risk:TRAP-RETENTION ✓, risk:TRAP-REALTIME ✗

Missed core (5): COM-RUN, INT-1c, INT-2b, INT-3b, SEC-REG

Wrong priority: FR-9 (FR-23: must, expected should), SEC-SIU (NFR-13: should, expected must)

Split obligations: FR-8a → FR-20, FR-21; INT-SFTP → INT-06, INT-07

### eval-20261121-230151-2

Model `qwen2.5:7b`; prompts: analyze_risks=1.2.0, critic=1.0.0, design_approach=2.0.0, executive_summary=1.0.0, extract_requirements=1.4.0

Trap checks: priority:LANG-ZH ✓, priority:LANG-BM ✓, buried:FR-UI ✓, buried:FR-EXPLAIN ✓, risk:TRAP-TIMELINE ✗, risk:TRAP-RETENTION ✓, risk:TRAP-REALTIME ✗

Missed core (5): COM-RUN, INT-1c, INT-2b, INT-3b, SEC-REG

Wrong priority: FR-9 (FR-23: must, expected should), SEC-SIU (NFR-13: should, expected must)

Split obligations: FR-8a → FR-20, FR-21; INT-SFTP → INT-06, INT-07
