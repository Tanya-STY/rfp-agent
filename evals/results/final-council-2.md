# Eval results

Gold: `evals/rfps/rfp_adversarial_council.md` (13 core / 2 optional requirements, 2 planted risks; status: **draft**). Generated 2026-11-22 00:30.

| Metric | eval-20261122-002816-1 |
|---|---:|
| Schema valid | yes |
| Requirements extracted | 14 |
| Recall: core gold | 100% |
| Recall: core gold, must | 100% |
| Recall: core, quoted anywhere | 100% |
| Precision (matches any gold) | 100% |
| Precision, one per obligation | 100% |
| False positives | 0 |
| Split obligations (extra preds) | 0 |
| Priority accuracy (matched core) | 92% |
| Grounded quotes | 100% |
| Dropped as ungrounded | 0 |
| Trap checks passed | 6/6 |
| Planted risks found + cited | 2/2 |
| Expected risks found | 0 |
| Approach covers must reqs | 100% |
| Critic passed | yes |
| Revisions | 0 |
| Wall time (min) | 2.50 |
| LLM calls | 13 |
| Prompt tokens | 13,028 |
| Completion tokens | 3,601 |

## Per-run detail

### eval-20261122-002816-1

Model `qwen2.5:7b`; prompts: analyze_risks=1.2.0, critic=1.0.0, design_approach=2.0.0, executive_summary=1.0.0, extract_requirements=1.4.0

Trap checks: priority:R1 ✓, priority:R4 ✓, priority:R7 ✓, forbidden:northgate ✓, risk:TRAP-HOSTING-CONTRADICTION ✓, risk:TRAP-NO-TIMELINE ✓

Missed core (0): none

Wrong priority: R2 (FR-02: must, expected should)
