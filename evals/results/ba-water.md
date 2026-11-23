# Eval results

Gold: `evals/rfps/rfp_water_fieldops.md` (26 core / 5 optional requirements, 3 planted risks; status: **draft**). Generated 2026-11-21 20:18.

| Metric | base-water | after-water |
|---|---:|---:|
| Schema valid | yes | yes |
| Requirements extracted | 27 | 30 |
| Recall: core gold | 92% | 100% |
| Recall: core gold, must | 95% | 100% |
| Recall: core, quoted anywhere | 96% | 100% |
| Precision (matches any gold) | 100% | 100% |
| Precision, one per obligation | 96% | 93% |
| False positives | 0 | 0 |
| Split obligations (extra preds) | 1 | 2 |
| Priority accuracy (matched core) | 100% | 100% |
| Grounded quotes | 100% | 100% |
| Dropped as ungrounded | 0 | 0 |
| Trap checks passed | 4/7 | 6/7 |
| Planted risks found + cited | 2/3 | 2/3 |
| Expected risks found | 0 | 0 |
| Approach covers must reqs | 100% | 100% |
| Judge: requirement faithful | 85% | 100% |
| Judge: priority reasonable | 100% | 95% |
| Judge: approach specificity (1-5) | 3.83 | 3.83 |
| Judge: constraint violations | 0 | 0 |
| Judge: risk specificity (1-5) | 3.40 | 4.60 |
| Judge: mitigation quality (1-5) | 5.00 | 5.00 |
| Judge time (min) | 1.00 | 1.00 |
| Critic passed | yes | yes |
| Revisions | 0 | 0 |
| Wall time (min) | 4.40 | 4.40 |
| LLM calls | 14 | 14 |
| Prompt tokens | 18,697 | 17,779 |
| Completion tokens | 6,165 | 6,352 |

## Across runs

| Metric | mean | sd |
|---|---:|---:|
| Requirements extracted | 28.5 | 2.1 |
| Recall: core gold | 96.2% | 5.4% |
| Recall: core gold, must | 97.6% | 3.4% |
| Recall: core, quoted anywhere | 98.1% | 2.7% |
| Precision (matches any gold) | 100.0% | 0.0% |
| Precision, one per obligation | 94.8% | 2.1% |
| False positives | 0.0 | 0.0 |
| Split obligations (extra preds) | 1.5 | 0.7 |
| Priority accuracy (matched core) | 100.0% | 0.0% |
| Grounded quotes | 100.0% | 0.0% |
| Dropped as ungrounded | 0.0 | 0.0 |
| Expected risks found | 0.0 | 0.0 |
| Approach covers must reqs | 100.0% | 0.0% |
| Judge: requirement faithful | 92.5% | 10.6% |
| Judge: priority reasonable | 97.5% | 3.5% |
| Judge: approach specificity (1-5) | 3.8 | 0.0 |
| Judge: constraint violations | 0.0 | 0.0 |
| Judge: risk specificity (1-5) | 4.0 | 0.8 |
| Judge: mitigation quality (1-5) | 5.0 | 0.0 |
| Judge time (min) | 1.0 | 0.0 |
| Critic passed | 1.0 | 0.0 |
| Revisions | 0.0 | 0.0 |
| Wall time (min) | 4.4 | 0.0 |
| LLM calls | 14.0 | 0.0 |
| Prompt tokens | 18238.0 | 649.1 |
| Completion tokens | 6258.5 | 132.2 |

Consistency: mean pairwise Jaccard of core items found **0.92**; 24 core items found in every run, 26 in at least one (of 26).

## Per-run detail

### base-water

Model `qwen2.5:7b`; prompts: analyze_risks=1.1.0, critic=1.0.0, design_approach=2.0.0, executive_summary=1.0.0, extract_requirements=1.3.0

Trap checks: priority:GIS ✓, priority:TL-PILOT ✗, buried:OFFLINE ✓, buried:VOICE ✗, risk:TRAP-UNION-TIMELINE ✗, risk:TRAP-VOICE-RECORDS ✓, risk:TRAP-RESPONSE-TIME ✓

Missed core (2): COM-CAP, VOICE

Split obligations: OFFLINE → FR-10, FR-11

### after-water

Model `qwen2.5:7b`; prompts: analyze_risks=1.1.0, critic=1.0.0, design_approach=2.0.0, executive_summary=1.0.0, extract_requirements=1.4.0

Trap checks: priority:GIS ✓, priority:TL-PILOT ✓, buried:OFFLINE ✓, buried:VOICE ✓, risk:TRAP-UNION-TIMELINE ✗, risk:TRAP-VOICE-RECORDS ✓, risk:TRAP-RESPONSE-TIME ✓

Missed core (0): none

Split obligations: S1 → SEC-01, SEC-02; SCOPE-QA → FR-01, FR-02
