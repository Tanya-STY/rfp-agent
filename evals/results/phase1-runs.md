# Eval results

Gold: `inputs/rfp_synthetic_main.md` (57 core / 35 optional requirements, 3 planted risks; status: **draft**). Generated 2026-11-21 18:42.

| Metric | sample | live5 | live6 | live7 | live8 | live9 |
|---|---:|---:|---:|---:|---:|---:|
| Schema valid | yes | yes | yes | yes | yes | yes |
| Requirements extracted | 94 | 94 | 91 | 91 | 78 | 76 |
| Recall: core gold | 82% | 82% | 86% | 86% | 82% | 84% |
| Recall: core gold, must | 83% | 80% | 85% | 85% | 78% | 83% |
| Recall: core, quoted anywhere | 93% | 95% | 96% | 96% | 96% | 96% |
| Precision (matches any gold) | 78% | 82% | 92% | 92% | 96% | 100% |
| Precision, one per obligation | 77% | 79% | 85% | 85% | 95% | 99% |
| False positives | 21 | 17 | 7 | 7 | 3 | 0 |
| Split obligations (extra preds) | 1 | 3 | 7 | 7 | 1 | 1 |
| Priority accuracy (matched core) | 87% | 96% | 96% | 96% | 94% | 96% |
| Grounded quotes | 100% | 100% | 100% | 100% | 100% | 100% |
| Dropped as ungrounded | 0 | 7 | 0 | 0 | 0 | 0 |
| Trap checks passed | 2/7 | 5/7 | 6/7 | 6/7 | 6/7 | 7/7 |
| Planted risks found + cited | 1/3 | 1/3 | 2/3 | 2/3 | 2/3 | 3/3 |
| Expected risks found | 1 | 1 | 2 | 2 | 2 | 2 |
| Approach covers must reqs | 100% | 75% | 86% | 100% | 100% | 100% |
| Critic passed | yes | no | no | yes | yes | yes |
| Revisions | 2 | 2 | 2 | 1 | 2 | 0 |
| Wall time (min) | 72.8 | 19.2 | 17.0 | 14.5 | 21.1 | 11.1 |
| LLM calls | 46 | 50 | 50 | 47 | 62 | 30 |
| Prompt tokens | 53,539 | 89,613 | 74,516 | 57,288 | 81,400 | 39,816 |
| Completion tokens | 20,214 | 26,082 | 24,283 | 21,181 | 29,902 | 16,485 |

## Across runs

| Metric | mean | sd |
|---|---:|---:|
| Requirements extracted | 87.3 | 8.1 |
| Recall: core gold | 84.0% | 1.7% |
| Recall: core gold, must | 82.2% | 2.5% |
| Recall: core, quoted anywhere | 95.6% | 1.5% |
| Precision (matches any gold) | 90.1% | 8.6% |
| Precision, one per obligation | 86.4% | 8.8% |
| False positives | 9.2 | 8.2 |
| Split obligations (extra preds) | 3.3 | 2.9 |
| Priority accuracy (matched core) | 94.0% | 3.5% |
| Grounded quotes | 100.0% | 0.0% |
| Dropped as ungrounded | 1.2 | 2.9 |
| Expected risks found | 1.7 | 0.5 |
| Approach covers must reqs | 93.5% | 10.7% |
| Critic passed | 0.7 | 0.5 |
| Revisions | 1.5 | 0.8 |
| Wall time (min) | 25.9 | 23.2 |
| LLM calls | 47.5 | 10.3 |
| Prompt tokens | 66028.7 | 18889.3 |
| Completion tokens | 23024.5 | 4739.1 |

Consistency: mean pairwise Jaccard of core items found **0.89**; 39 core items found in every run, 54 in at least one (of 57).

## Per-run detail

### sample

Model `qwen2.5:7b`; prompts: analyze_risks=1.0.0, critic=1.0.0, design_approach=1.0.0, executive_summary=1.0.0, extract_requirements=1.1.0

Trap checks: priority:LANG-ZH ✗, priority:LANG-BM ✗, buried:FR-UI ✗, buried:FR-EXPLAIN ✓, risk:TRAP-TIMELINE ✗, risk:TRAP-RETENTION ✗, risk:TRAP-REALTIME ✓

Missed core (10): COM-RUN, FR-5b, FR-UI, INT-1a, INT-3a, LANG-ZH, SEC-3b, SEC-4a, SEC-5b, TEAM-MY

Wrong priority: FR-9 (FR-21: must, expected should), LANG-BM (FR-24: could, expected should), NFR-1a (NFR-04: must, expected should), NFR-1b (NFR-05: must, expected should), SEC-SIU (NFR-14: should, expected must), TEAM-NAMED (COM-13: should, expected must)

Split obligations: LANG-BM → FR-24, FR-25

False positives (21):

- NFR-02 Historical claim documents: "Roughly 9 TB of historical claim documents exist, of which approximately 2.1 million docum"
- NFR-03 Two data centres: "The Company operates two data centres in Malaysia (primary in Cyberjaya, secondary in Joho"
- SEC-09 Technical architecture evaluation: "Technical architecture, security and compliance | 25%"
- INT-01 Use ClaimsNet: "Claims are managed in **ClaimsNet**, an in-house claims management system built on Java an"
- INT-02 Limited SOAP web services: "ClaimsNet exposes a limited set of SOAP web services; there is no REST API today, and the "
- INT-03 Use IBM MQ: "Policy data sits in a mainframe-hosted policy administration system (PAS) that is accessed"
- INT-05 Use DMS: "Documents are stored in a document management system (DMS) on a network file share, with m"
- COM-15 Solution fit evaluation: "Solution fit to functional and non-functional requirements | 30%"
- COM-16 Delivery approach evaluation: "Delivery approach, timeline realism and team | 20%"
- COM-17 Commercial value evaluation: "Commercial value and total cost of ownership | 15%"
- COM-18 Capability transfer evaluation: "Capability transfer and ongoing support | 10%"
- COM-19 Electronic submission: "Proposals must be submitted electronically to the procurement portal by the due date state"
- COM-20 Executive summary length: "Proposals should contain:

1. An executive summary of no more than two pages."
- COM-21 Requirements compliance matrix: "2. A requirements compliance matrix responding to every FR, NFR, INT and SEC requirement."
- COM-22 Solution architecture: "3. Solution architecture, including a deployment diagram showing where every component run"
- COM-23 Delivery plan and milestones: "4. Delivery plan and milestones, with key assumptions and dependencies on Corvane."
- COM-24 Team structure and CVs: "5. Team structure and CVs of named personnel."
- COM-25 Commercial proposal: "6. Commercial proposal, in a separate document."
- COM-26 Risks and mitigations: "7. Risks and proposed mitigations."
- COM-27 Proposal length: "The main body of the proposal should not exceed 40 pages excluding appendices."
- COM-28 Clarification questions submission: "Clarification questions must be submitted in writing through the procurement portal by 5 F"

### live5

Model `qwen2.5:7b`; prompts: analyze_risks=1.0.0, critic=1.0.0, design_approach=2.0.0, executive_summary=1.0.0, extract_requirements=1.3.0

Trap checks: priority:LANG-ZH ✓, priority:LANG-BM ✓, buried:FR-UI ✓, buried:FR-EXPLAIN ✓, risk:TRAP-TIMELINE ✗, risk:TRAP-RETENTION ✗, risk:TRAP-REALTIME ✓

Missed core (10): COM-RUN, FR-5b, FR-7b, INT-3b, NFR-3b, SEC-3a, SEC-4a, SEC-5b, SEC-REG, TEAM-MY

Wrong priority: FR-9 (FR-22: must, expected should), SEC-SIU (NFR-18: should, expected must)

Split obligations: ENV-2 → NFR-05, NFR-06; FR-8a → FR-18, FR-19, FR-20

False positives (17):

- NFR-03 Store documents on network file share: "Documents are stored in a document management system (DMS) on a network file share, with m"
- NFR-04 Historical claim documents storage: "Roughly 9 TB of historical claim documents exist, of which approximately 2.1 million docum"
- NFR-07 Two data centres in Malaysia: "The Company operates two data centres in Malaysia (primary in Cyberjaya, secondary in Joho"
- NFR-08 Limited use of Microsoft Azure: "The Company operates two data centres in Malaysia (primary in Cyberjaya, secondary in Joho"
- NFR-20 Executive summary length: "Proposals should contain:

1. An executive summary of no more than two pages."
- NFR-21 Proposal length limit: "The main body of the proposal should not exceed 40 pages excluding appendices."
- SEC-08 Technical architecture evaluation: "| Technical architecture, security and compliance | 25% |"
- INT-01 Use ClaimsNet: "Claims are managed in **ClaimsNet**, an in-house claims management system built on Java an"
- INT-02 No REST API: "ClaimsNet exposes a limited set of SOAP web services; there is no REST API today, and the "
- INT-03 Use IBM MQ for PAS: "Policy data sits in a mainframe-hosted policy administration system (PAS) that is accessed"
- COM-18 Solution fit evaluation: "| Solution fit to functional and non-functional requirements | 30% |"
- COM-19 Delivery approach evaluation: "| Delivery approach, timeline realism and team | 20% |"
- COM-20 Commercial value evaluation: "| Commercial value and total cost of ownership | 15% |"
- COM-21 Capability transfer evaluation: "| Capability transfer and ongoing support | 10% |"
- COM-22 Electronic submission: "Proposals must be submitted electronically to the procurement portal by the due date state"
- COM-23 Due date for submission: "Proposals must be submitted electronically to the procurement portal by the due date state"
- COM-24 Clarification questions submission: "Clarification questions must be submitted in writing through the procurement portal by 5 F"

### live6

Model `qwen2.5:7b`; prompts: analyze_risks=1.1.0, critic=1.0.0, design_approach=2.0.0, executive_summary=1.0.0, extract_requirements=1.3.0

Trap checks: priority:LANG-ZH ✓, priority:LANG-BM ✓, buried:FR-UI ✓, buried:FR-EXPLAIN ✓, risk:TRAP-TIMELINE ✗, risk:TRAP-RETENTION ✓, risk:TRAP-REALTIME ✓

Missed core (8): COM-RUN, FR-5b, FR-7b, INT-3b, SEC-3a, SEC-4a, SEC-5b, SEC-REG

Wrong priority: FR-9 (FR-22: must, expected should), SEC-SIU (NFR-19: should, expected must)

Split obligations: ENV-2 → NFR-05, NFR-06; EVAL-1 → NFR-20, NFR-21, NFR-22, NFR-23, NFR-24; FR-8a → FR-18, FR-19, FR-20

False positives (7):

- NFR-03 Store documents on network file share: "Documents are stored in a document management system (DMS) on a network file share, with m"
- NFR-04 Historical claim documents storage: "Roughly 9 TB of historical claim documents exist, of which approximately 2.1 million docum"
- NFR-07 Two data centres in Malaysia: "The Company operates two data centres in Malaysia (primary in Cyberjaya, secondary in Joho"
- NFR-08 Limited use of Microsoft Azure: "The Company operates two data centres in Malaysia (primary in Cyberjaya, secondary in Joho"
- INT-01 Use ClaimsNet: "Claims are managed in **ClaimsNet**, an in-house claims management system built on Java an"
- INT-02 No REST API: "ClaimsNet exposes a limited set of SOAP web services; there is no REST API today, and the "
- INT-03 Use IBM MQ for PAS: "Policy data sits in a mainframe-hosted policy administration system (PAS) that is accessed"

### live7

Model `qwen2.5:7b`; prompts: analyze_risks=1.1.0, critic=1.0.0, design_approach=2.0.0, executive_summary=1.0.0, extract_requirements=1.3.0

Trap checks: priority:LANG-ZH ✓, priority:LANG-BM ✓, buried:FR-UI ✓, buried:FR-EXPLAIN ✓, risk:TRAP-TIMELINE ✗, risk:TRAP-RETENTION ✓, risk:TRAP-REALTIME ✓

Missed core (8): COM-RUN, FR-5b, FR-7b, INT-3b, SEC-3a, SEC-4a, SEC-5b, SEC-REG

Wrong priority: FR-9 (FR-22: must, expected should), SEC-SIU (NFR-19: should, expected must)

Split obligations: ENV-2 → NFR-05, NFR-06; EVAL-1 → NFR-20, NFR-21, NFR-22, NFR-23, NFR-24; FR-8a → FR-18, FR-19, FR-20

False positives (7):

- NFR-03 Store documents on network file share: "Documents are stored in a document management system (DMS) on a network file share, with m"
- NFR-04 Historical claim documents storage: "Roughly 9 TB of historical claim documents exist, of which approximately 2.1 million docum"
- NFR-07 Two data centres in Malaysia: "The Company operates two data centres in Malaysia (primary in Cyberjaya, secondary in Joho"
- NFR-08 Limited use of Microsoft Azure: "The Company operates two data centres in Malaysia (primary in Cyberjaya, secondary in Joho"
- INT-01 Use ClaimsNet: "Claims are managed in **ClaimsNet**, an in-house claims management system built on Java an"
- INT-02 No REST API: "ClaimsNet exposes a limited set of SOAP web services; there is no REST API today, and the "
- INT-03 Use IBM MQ for PAS: "Policy data sits in a mainframe-hosted policy administration system (PAS) that is accessed"

### live8

Model `qwen2.5:7b`; prompts: analyze_risks=1.1.0, critic=1.0.0, design_approach=2.0.0, executive_summary=1.0.0, extract_requirements=1.3.0

Trap checks: priority:LANG-ZH ✓, priority:LANG-BM ✓, buried:FR-UI ✓, buried:FR-EXPLAIN ✓, risk:TRAP-TIMELINE ✗, risk:TRAP-RETENTION ✓, risk:TRAP-REALTIME ✓

Missed core (10): COM-BUDGET, FR-5b, FR-7b, INT-2b, INT-3b, SEC-3b, SEC-4a, SEC-5b, SEC-REG, SEC-SIU

Wrong priority: FR-9 (FR-22: must, expected should), SCOPE-7 (COM-02: should, expected must), SEC-DEL (SEC-08: should, expected must)

Split obligations: FR-8a → FR-19, FR-20

False positives (3):

- NFR-01 Claims settlement not in scope: "- Claims settlement and payment processing."
- NFR-02 Policy admin system core logic changes not in scope: "- Changes to the policy administration system's core logic."
- NFR-04 Life and medical insurance claims out of scope: "- Life and medical insurance claims, which are handled by our affiliate and are not part o"

### live9

Model `qwen2.5:7b`; prompts: analyze_risks=1.1.0, critic=1.0.0, design_approach=2.0.0, executive_summary=1.0.0, extract_requirements=1.3.0

Trap checks: priority:LANG-ZH ✓, priority:LANG-BM ✓, buried:FR-UI ✓, buried:FR-EXPLAIN ✓, risk:TRAP-TIMELINE ✓, risk:TRAP-RETENTION ✓, risk:TRAP-REALTIME ✓

Missed core (9): COM-RUN, FR-5b, FR-7b, INT-2b, INT-3b, SEC-3a, SEC-4a, SEC-5b, SEC-REG

Wrong priority: FR-9 (FR-21: must, expected should), SEC-SIU (NFR-14: should, expected must)

Split obligations: FR-8a → FR-18, FR-19
