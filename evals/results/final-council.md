# Eval results

Gold: `evals/rfps/rfp_adversarial_council.md` (13 core / 2 optional requirements, 2 planted risks; status: **draft**). Generated 2026-11-21 23:29.

| Metric | eval-20261121-232400-1 | eval-20261121-232400-2 |
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
| Trap checks passed | 6/6 | 6/6 |
| Planted risks found + cited | 2/2 | 2/2 |
| Expected risks found | 0 | 1 |
| Approach covers must reqs | 100% | 100% |
| Critic passed | yes | yes |
| Revisions | 0 | 0 |
| Wall time (min) | 2.80 | 2.50 |
| LLM calls | 14 | 13 |
| Prompt tokens | 14,488 | 12,983 |
| Completion tokens | 4,023 | 3,585 |

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
| Expected risks found | 0.5 | 0.7 |
| Approach covers must reqs | 100.0% | 0.0% |
| Critic passed | 1.0 | 0.0 |
| Revisions | 0.0 | 0.0 |
| Wall time (min) | 2.6 | 0.2 |
| LLM calls | 13.5 | 0.7 |
| Prompt tokens | 13735.5 | 1064.2 |
| Completion tokens | 3804.0 | 309.7 |

Consistency: mean pairwise Jaccard of core items found **1.00**; 13 core items found in every run, 13 in at least one (of 13).

## Per-run detail

### eval-20261121-232400-1

Model `qwen2.5:7b`; prompts: analyze_risks=1.2.0, critic=1.0.0, design_approach=2.0.0, executive_summary=1.0.0, extract_requirements=1.4.0

Trap checks: priority:R1 ✓, priority:R4 ✓, priority:R7 ✓, forbidden:northgate ✓, risk:TRAP-HOSTING-CONTRADICTION ✓, risk:TRAP-NO-TIMELINE ✓

Missed core (0): none

Wrong priority: R2 (FR-02: must, expected should)

### eval-20261121-232400-2

Model `qwen2.5:7b`; prompts: analyze_risks=1.2.0, critic=1.0.0, design_approach=2.0.0, executive_summary=1.0.0, extract_requirements=1.4.0

Trap checks: priority:R1 ✓, priority:R4 ✓, priority:R7 ✓, forbidden:northgate ✓, risk:TRAP-HOSTING-CONTRADICTION ✓, risk:TRAP-NO-TIMELINE ✓

Missed core (0): none

Wrong priority: R2 (FR-02: must, expected should)
