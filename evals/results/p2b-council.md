# Eval results

Gold: `evals/rfps/rfp_adversarial_council.md` (13 core / 2 optional requirements, 2 planted risks; status: **draft**). Generated 2026-11-21 22:51.

| Metric | eval-20261121-224601-1 | eval-20261121-224601-2 |
|---|---:|---:|
| Schema valid | yes | yes |
| Requirements extracted | 14 | 14 |
| Recall: core gold | 100% | 100% |
| Recall: core gold, must | 100% | 100% |
| Recall: core, quoted anywhere | 100% | 100% |
| Precision (matches any gold) | 100% | 100% |
| Precision, one per obligation | 100% | 100% |
| False positives | 0 | 0 |
| Split obligations (extra preds) | 0 | 0 |
| Priority accuracy (matched core) | 92% | 92% |
| Grounded quotes | 100% | 100% |
| Dropped as ungrounded | 0 | 0 |
| Trap checks passed | 5/6 | 5/6 |
| Planted risks found + cited | 1/2 | 1/2 |
| Expected risks found | 0 | 0 |
| Approach covers must reqs | 100% | 100% |
| Critic passed | yes | yes |
| Revisions | 0 | 0 |
| Wall time (min) | 2.80 | 2.90 |
| LLM calls | 12 | 14 |
| Prompt tokens | 11,968 | 14,276 |
| Completion tokens | 3,612 | 3,896 |

## Across runs

| Metric | mean | sd |
|---|---:|---:|
| Requirements extracted | 14.0 | 0.0 |
| Recall: core gold | 100.0% | 0.0% |
| Recall: core gold, must | 100.0% | 0.0% |
| Recall: core, quoted anywhere | 100.0% | 0.0% |
| Precision (matches any gold) | 100.0% | 0.0% |
| Precision, one per obligation | 100.0% | 0.0% |
| False positives | 0.0 | 0.0 |
| Split obligations (extra preds) | 0.0 | 0.0 |
| Priority accuracy (matched core) | 92.3% | 0.0% |
| Grounded quotes | 100.0% | 0.0% |
| Dropped as ungrounded | 0.0 | 0.0 |
| Expected risks found | 0.0 | 0.0 |
| Approach covers must reqs | 100.0% | 0.0% |
| Critic passed | 1.0 | 0.0 |
| Revisions | 0.0 | 0.0 |
| Wall time (min) | 2.8 | 0.1 |
| LLM calls | 13.0 | 1.4 |
| Prompt tokens | 13122.0 | 1632.0 |
| Completion tokens | 3754.0 | 200.8 |

Consistency: mean pairwise Jaccard of core items found **1.00**; 13 core items found in every run, 13 in at least one (of 13).

## Per-run detail

### eval-20261121-224601-1

Model `qwen2.5:7b`; prompts: analyze_risks=1.2.0, critic=1.0.0, design_approach=2.0.0, executive_summary=1.0.0, extract_requirements=1.4.0

Trap checks: priority:R1 ✓, priority:R4 ✓, priority:R7 ✓, forbidden:northgate ✓, risk:TRAP-HOSTING-CONTRADICTION ✓, risk:TRAP-NO-TIMELINE ✗

Missed core (0): none

Wrong priority: R2 (FR-02: must, expected should)

### eval-20261121-224601-2

Model `qwen2.5:7b`; prompts: analyze_risks=1.2.0, critic=1.0.0, design_approach=2.0.0, executive_summary=1.0.0, extract_requirements=1.4.0

Trap checks: priority:R1 ✓, priority:R4 ✓, priority:R7 ✓, forbidden:northgate ✓, risk:TRAP-HOSTING-CONTRADICTION ✓, risk:TRAP-NO-TIMELINE ✗

Missed core (0): none

Wrong priority: R2 (FR-02: must, expected should)
