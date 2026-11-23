# Eval results

Gold: `inputs/rfp_synthetic_main.md` (57 core / 35 optional requirements, 3 planted risks; status: **reviewed**). Generated 2026-11-22 21:03.

| Metric | eval-20261122-204928-1 |
|---|---:|
| Schema valid | yes |
| Requirements extracted | 82 |
| Recall: core gold | 93% |
| Recall: core gold, must | 96% |
| Recall: core, quoted anywhere | 93% |
| Precision (matches any gold) | 100% |
| Precision, one per obligation | 98% |
| False positives | 0 |
| Split obligations (extra preds) | 2 |
| Priority accuracy (matched core) | 96% |
| Grounded quotes | 100% |
| Dropped as ungrounded | 0 |
| Trap checks passed | 6/6 |
| Planted risks found + cited | 3/3 |
| Expected risks found | 1 |
| Approach covers must reqs | 100% |
| Critic passed | yes |
| Revisions | 1 |
| Wall time (min) | 14.4 |
| LLM calls | 48 |
| Prompt tokens | 61,762 |
| Completion tokens | 21,006 |

## Per-run detail

### eval-20261122-204928-1

Model `qwen2.5:7b`; prompts: analyze_risks=1.2.0, critic=1.0.0, design_approach=2.0.0, executive_summary=1.0.0, extract_requirements=1.4.0

Trap checks: priority:LANG-ZH ✓, buried:FR-UI ✓, buried:FR-EXPLAIN ✓, risk:TRAP-TIMELINE ✓, risk:TRAP-RETENTION ✓, risk:TRAP-REALTIME ✓

Missed core (4): COM-RUN, INT-1c, INT-3b, SEC-REG

Wrong priority: FR-9 (FR-23: must, expected should), SEC-SIU (NFR-13: should, expected must)

Split obligations: FR-8a → FR-20, FR-21; INT-SFTP → INT-07, INT-08
