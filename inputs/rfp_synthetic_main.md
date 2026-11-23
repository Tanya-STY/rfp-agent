# Request for Proposal: Intelligent Claims Triage and Document Intelligence Platform

**Issuing organisation:** Corvane Mutual Assurance Berhad ("Corvane", "the Company")
**RFP reference:** CMA-IT-2027-014
**Issue date:** 12 January 2027
**Proposal due date:** 26 February 2027, 17:00 local time

---

## 1. Introduction and Background

Corvane Mutual Assurance is a mid-sized general insurer with approximately 1.4 million active policies across motor, home, travel and small-commercial property lines. The Company has operated for over forty years and is headquartered in Kuala Lumpur, with regional claims offices in Penang, Johor Bahru and Kota Kinabalu. Corvane processes roughly 210,000 claims per year, of which about 70% are motor claims.

Claims are currently lodged through four channels: the customer web portal, the mobile app, email to regional claims inboxes, and paper forms submitted at branches or by brokers. Paper and email claims are scanned and keyed in manually by a back-office team of 38 claims administrators. Each claim typically arrives with between three and twelve supporting documents: claim forms, police reports, repair estimates, medical receipts, photographs, invoices and, increasingly, WhatsApp screenshots forwarded by customers.

Our internal review in 2026 found that the average time from first notification of loss (FNOL) to a claim being assigned to the correct adjuster is 3.8 working days. Around 22% of claims are routed to the wrong team at least once. Adjusters report spending close to 40% of their time reading and re-keying documents rather than assessing claims. Customer satisfaction with the claims process (measured by post-claim survey) has fallen from 78% to 64% over three years, and two competitors now advertise same-day claim acknowledgement with a named handler.

The Board has approved a multi-year Claims Modernisation Programme. This RFP covers the first and most important workstream of that programme: an AI-enabled platform to read, classify and triage incoming claims and their documents, and to put the right information in front of the right adjuster quickly.

## 2. Objectives

Corvane's objectives for this engagement are to:

1. Reduce the average time from FNOL to correct adjuster assignment from 3.8 working days to under 4 working hours for straightforward claims.
2. Reduce misrouted claims from 22% to below 5%.
3. Cut manual document keying effort by at least 60% within twelve months of go-live.
4. Give adjusters a concise, trustworthy summary of each claim so they can start assessment without opening every attachment.
5. Improve early detection of potentially fraudulent claims by surfacing anomalies to the Special Investigations Unit (SIU), without automatically declining any claim.

We want a partner who will help us build lasting internal capability, not a black box. Corvane's own data science team (currently six people) must be able to understand, maintain and retrain the solution after handover.

## 3. Scope of Work

### 3.1 In scope

- Ingestion of claim documents from all four lodgement channels.
- Document classification, data extraction and claim summarisation.
- Triage: complexity scoring, line-of-business routing and adjuster queue assignment.
- Fraud-indicator flagging for referral to SIU.
- An adjuster-facing view of the AI outputs (see section 6 regarding where this must live).
- Monitoring, evaluation and model governance tooling for the AI components.
- Knowledge transfer and training for Corvane's IT, data science and claims teams.

### 3.2 Out of scope

- Claims settlement and payment processing.
- Changes to the policy administration system's core logic.
- Customer-facing chatbots. A separate initiative is evaluating conversational channels and bidders should not propose one here.
- Life and medical insurance claims, which are handled by our affiliate and are not part of this programme.

Bidders may propose optional extensions, priced separately, but these will not be scored as part of the core evaluation.

## 4. Current Environment

Claims are managed in **ClaimsNet**, an in-house claims management system built on Java and an Oracle 12c database in 2011. ClaimsNet exposes a limited set of SOAP web services; there is no REST API today, and the vendor team that built it has largely moved on. Batch interfaces run nightly via flat files on an SFTP server.

Policy data sits in a mainframe-hosted policy administration system (PAS) that is accessed through a message queue integration layer (IBM MQ). Read access to policy coverage details is possible in near real time; write access is not permitted for this project.

Documents are stored in a document management system (DMS) on a network file share, with metadata held in ClaimsNet. Roughly 9 TB of historical claim documents exist, of which approximately 2.1 million documents relate to claims closed in the last five years and may be usable for training and evaluation, subject to the data protection constraints in section 8.

Identity is managed through on-premise Active Directory. All internal applications must use single sign-on.

The Company operates two data centres in Malaysia (primary in Cyberjaya, secondary in Johor) and has a limited Microsoft Azure footprint (Southeast Asia region) used today only for email and collaboration tools.

## 5. Functional Requirements

The following requirements are numbered for reference in proposals. Bidders must state for each whether it is met out of the box, met through configuration, met through custom development, or not met.

**FR-1 Multi-channel ingestion.** The solution shall ingest claim documents from the web portal, mobile app, monitored email inboxes and scanned paper batches, and associate every document with the correct claim number in ClaimsNet.

**FR-2 Document classification.** The solution shall classify each incoming document into Corvane's document taxonomy (currently 27 document types, to be provided after contract award) with a confidence score.

**FR-3 Data extraction.** The solution shall extract key fields from claim forms, police reports, repair estimates and invoices, including at minimum: policy number, incident date, incident location, vehicle registration (motor), third-party details, itemised amounts and totals.

**FR-4 Handwriting and image quality.** The solution shall handle handwritten claim forms and low-quality phone photographs of documents, and shall flag documents that cannot be read reliably rather than guessing.

**FR-5 Claim summarisation.** The solution shall generate a plain-language summary of each claim (no more than 200 words) for the assigned adjuster, highlighting the incident, the parties involved, amounts claimed and any missing documents. Every factual statement in the summary must be traceable to a source document.

**FR-6 Triage and routing.** The solution shall assign each claim a complexity score and route it to the appropriate line-of-business queue and adjuster tier, using rules configurable by Corvane's claims operations team without vendor involvement.

**FR-7 Fraud indicators.** The solution shall identify potential fraud indicators (for example, inconsistent dates, duplicate invoices across claims, altered documents) and refer flagged claims to SIU with an explanation. The solution must never automatically decline or close a claim.

**FR-8 Human review.** Adjusters shall be able to accept, correct or reject every AI-generated classification, extracted field and summary. Corrections shall be captured and made available for model improvement.

**FR-9 Missing information requests.** Where mandatory documents are missing, the solution should draft a request to the customer for the adjuster to review and send.

**FR-10 Reporting.** The solution shall provide operational dashboards covering volumes, processing times, routing accuracy, extraction accuracy and adjuster override rates.

Adjusters have been clear in workshops that they will not adopt a tool that forces them to switch between screens all day. Whatever the solution produces needs to appear inside the ClaimsNet claim screen that adjusters already work in, or at minimum be reachable from it in a single click with the claim context already loaded.

Corvane's claims operations managers have also asked that every routing decision be explainable in business terms, so that when a customer or the regulator asks why a claim was handled in a certain way, a team leader can answer without involving IT.

## 6. Non-Functional Requirements

**NFR-1 Performance.** Classification and extraction for a single document should complete within 30 seconds of receipt at the 95th percentile. Triage and routing for a complete claim should be available to the adjuster in real time once all FNOL documents are received.

**NFR-2 Throughput.** The solution shall sustain peak volumes of 2,500 claims per day (approximately three times the daily average), as experienced during the year-end monsoon flooding season, without degradation beyond the targets in NFR-1.

**NFR-3 Availability.** The production service shall achieve 99.5% availability during business hours (08:00 to 20:00, Monday to Saturday). Planned maintenance must be scheduled outside these hours.

**NFR-4 Resilience.** If the AI components are unavailable, claims must continue to flow into ClaimsNet using the existing manual process, with no loss of documents.

**NFR-5 Scalability.** The architecture should allow other lines of business and additional document types to be onboarded by Corvane staff without re-architecture.

**NFR-6 Accessibility and usability.** Adjuster-facing interfaces shall meet WCAG 2.1 AA.

**NFR-7 Maintainability.** All models, prompts and configuration shall be version-controlled, and every production output shall be traceable to the model and configuration version that produced it.

## 7. Integration Requirements and Constraints

**INT-1** Integration with ClaimsNet shall use the existing SOAP services where they exist. Where new interfaces are required, the bidder shall describe how they will be built and who will maintain them. Corvane prefers not to modify ClaimsNet's core codebase; minor additions to its user interface are acceptable if delivered through its plugin framework.

**INT-2** Policy coverage lookups shall use the existing IBM MQ integration layer. The solution shall not write to the policy administration system.

**INT-3** Documents shall continue to be stored in the existing DMS as the system of record. The solution may hold working copies only for as long as needed for processing, subject to the retention rules in section 8.

**INT-4** The solution shall authenticate users through Corvane's Active Directory using single sign-on.

The nightly SFTP batch interfaces are expected to be retired within two years. Bidders should avoid designing new dependencies on them.

## 8. Security, Privacy and Compliance

Corvane is regulated by Bank Negara Malaysia (BNM) and must comply with the Personal Data Protection Act 2010 (PDPA) as amended, BNM's Risk Management in Technology (RMiT) policy, and its own information security standards.

**SEC-1 Data residency.** All customer personal data, claim documents and derived data (including extracted fields, embeddings and model outputs) must be stored and processed within Corvane's own Malaysian data centres. This includes inference by any AI or machine learning model. Use of public cloud services for processing customer data, including Malaysian cloud regions, is not permitted for this programme without prior approval from Corvane's Technology Risk Committee and notification to the regulator, a process that typically takes six to nine months.

**SEC-2 Personal data protection.** Claim documents contain personal data, including identity card numbers, health information from injury claims and bank account details. The solution shall minimise exposure of personal data, mask identity card numbers in all adjuster-facing summaries except where explicitly needed, and shall not use personal data for any purpose other than claims handling and the improvement of the claims models.

**SEC-3 Audit trail.** Every AI output, every human override, and every routing decision shall be logged with a timestamp, user or system identity, input references and the model version used. Audit logs shall be immutable and retained for seven years.

**SEC-4 Access control.** Access shall be role-based. SIU fraud flags shall be visible only to SIU staff and designated claims managers, not to all adjusters.

**SEC-5 Security testing.** The solution shall undergo independent penetration testing before go-live and annually thereafter. Findings rated high or critical must be remediated before go-live.

**SEC-6 Model risk.** The bidder shall support Corvane's model risk management process, including documentation of model purpose, training data, known limitations, evaluation results and bias testing across customer segments.

**SEC-7 Third-party models.** Where foundation models or large language models are used, the bidder shall disclose the model, its licence, where it is hosted, and confirm that no Corvane data is used to train third-party models.

Working copies of documents held by the solution must be deleted within 30 days of claim closure. Bidders should note that the same documents may be required for SIU investigations for considerably longer, and the solution design must accommodate this.

## 9. Timeline and Milestones

Corvane's Board has committed publicly to visible improvements in claims service during 2027. The target timeline is as follows:

| Milestone | Target date |
|---|---|
| Contract award | 31 March 2027 |
| Discovery and design complete | 15 May 2027 |
| Pilot go-live (motor claims, Kuala Lumpur office) | 30 June 2027 |
| Full motor rollout, all offices | 30 September 2027 |
| Home, travel and small-commercial lines live | 31 January 2028 |
| Handover to Corvane support | 31 March 2028 |

The pilot go-live date of 30 June 2027 is fixed and is linked to a commitment made to the Board. Bidders proposing a later pilot date will need to provide an exceptionally strong justification.

Corvane does not currently own GPU infrastructure in either data centre. Our infrastructure team estimates that procurement, delivery and installation of new server hardware typically takes 16 to 20 weeks from purchase order, and capital purchases above MYR 1 million require Board approval at its quarterly meeting. Bidders should describe their assumptions about compute infrastructure clearly.

## 10. Commercial Terms and Budget

The indicative budget envelope for this workstream is **MYR 6.5 million to MYR 8 million** over the initial contract term (contract award to handover), inclusive of software licences, implementation services and the first year of support, but exclusive of any hardware Corvane procures directly. Ongoing annual run costs after handover should not exceed MYR 1.2 million.

Bidders shall provide:

- A fixed price for discovery and design.
- A fixed or capped price for the pilot.
- A time-and-materials or fixed price, at the bidder's option, for the rollout phases, with rate cards.
- Annual licence and support costs for five years after handover.
- Any infrastructure or hardware the bidder recommends Corvane procure, with indicative costs, shown separately.

Payment will be milestone-based. Corvane expects at least 15% of the services fee to be linked to achievement of measurable outcomes, for example routing accuracy and keying effort reduction, measured after the pilot.

Corvane's standard terms require that all intellectual property in custom work products, including prompts, configurations, fine-tuned model weights and evaluation datasets created specifically for Corvane, vest in Corvane.

## 11. Bidder Experience, Team and Delivery Approach

Bidders should describe at least two comparable implementations in insurance or financial services, preferably in Southeast Asia, with client references.

The proposed team must include a named delivery lead and a named solution architect who will remain on the engagement through at least full motor rollout. Corvane expects a blended onshore and offshore team; however, any personnel with access to production data must be based in Malaysia and hold appropriate security clearance as determined by Corvane.

Bidders should explain how they will evaluate model quality before and after go-live, including how they will measure extraction accuracy, routing accuracy and summary faithfulness, and how they will detect drift once in production. Corvane's data science team will want to run these evaluations themselves after handover.

Many of our customers in Sabah and in the northern region correspond in Bahasa Malaysia, and a meaningful minority of documents (we estimate 10 to 15%) arrive in Chinese. Support for Bahasa Malaysia documents is expected from the pilot. If Chinese-language documents could also be handled, that would be welcome, although we recognise this may come later and it is not a condition of award.

## 12. Evaluation Criteria

Proposals will be evaluated by a panel drawn from Claims Operations, IT, Data Science, Technology Risk and Procurement, using the following weighted criteria:

| Criterion | Weight |
|---|---|
| Solution fit to functional and non-functional requirements | 30% |
| Technical architecture, security and compliance | 25% |
| Delivery approach, timeline realism and team | 20% |
| Commercial value and total cost of ownership | 15% |
| Capability transfer and ongoing support | 10% |

Corvane may shortlist up to three bidders for a two-hour solution demonstration using anonymised sample claims provided by Corvane. Shortlisted bidders may be asked to complete a short proof of concept at their own cost.

Corvane is not obliged to accept the lowest-priced or any proposal.

## 13. Submission Instructions

Proposals must be submitted electronically to the procurement portal by the due date stated above. Late submissions will not be considered.

Proposals should contain:

1. An executive summary of no more than two pages.
2. A requirements compliance matrix responding to every FR, NFR, INT and SEC requirement.
3. Solution architecture, including a deployment diagram showing where every component runs and where data is stored and processed.
4. Delivery plan and milestones, with key assumptions and dependencies on Corvane.
5. Team structure and CVs of named personnel.
6. Commercial proposal, in a separate document.
7. Risks and proposed mitigations.

The main body of the proposal should not exceed 40 pages excluding appendices. Clarification questions must be submitted in writing through the procurement portal by 5 February 2027; Corvane will publish anonymised answers to all bidders by 12 February 2027.

All information in this RFP is confidential and provided solely for the purpose of preparing a proposal.
