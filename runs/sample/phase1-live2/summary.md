# RFP Solution Summary - rfp_synthetic_main.md

_Run `live2` - model `qwen2.5:7b` - critic passed after 2 revision(s)_

## Executive summary

The client seeks to reduce FNOL to adjuster assignment time and misrouting of claims through an intelligent claims triage and document intelligence platform. The proposed solution will integrate with existing systems, provide claim summaries, and implement fraud detection while ensuring no claims are automatically declined. Key risks include potential conflicts with hardware procurement timelines, security compliance issues, and the risk of late hardware delivery.

## Requirements (94)

| ID | Priority | Title | Description | Source | Quote |
|---|---|---|---|---|---|
| FR-01 | must | Reduce FNOL to adjuster assignment time | Reduce average time from FNOL to correct adjuster assignment to under 4 working hours. | S03 | "Reduce the average time from FNOL to correct adjuster assignment from 3.8 working days to under 4 working hours for straightforward claims." |
| FR-02 | must | Reduce misrouted claims | Reduce misrouted claims from 22% to below 5%. | S03 | "Reduce misrouted claims from 22% to below 5%." |
| FR-03 | should | Provide concise claim summary | Provide adjusters with a concise, trustworthy summary of each claim. | S03 | "Give adjusters a concise, trustworthy summary of each claim so they can start assessment without opening every attachment." |
| FR-04 | should | Detect potential fraud | Detect and surface anomalies to the SIU for potentially fraudulent claims. | S03 | "Improve early detection of potentially fraudulent claims by surfacing anomalies to the Special Investigations Unit (SIU), without automatically declining any claim." |
| FR-05 | must | Ingest claim documents | Ingest claim documents from all four lodgement channels. | S04 | "- Ingestion of claim documents from all four lodgement channels." |
| FR-06 | must | Document classification and data extraction | Perform document classification, data extraction and claim summarisation. | S04 | "- Document classification, data extraction and claim summarisation." |
| FR-07 | must | Triage claims | Perform triage: complexity scoring, line-of-business routing and adjuster queue assignment. | S04 | "- Triage: complexity scoring, line-of-business routing and adjuster queue assignment." |
| FR-08 | must | Fraud indicator flagging | Flag claims for fraud indicators for referral to SIU. | S04 | "- Fraud-indicator flagging for referral to SIU." |
| FR-09 | should | Adjuster-facing AI outputs | Provide an adjuster-facing view of the AI outputs. | S04 | "- An adjuster-facing view of the AI outputs (see section 6 regarding where this must live)." |
| FR-10 | must | Monitoring and evaluation tooling | Provide monitoring, evaluation and model governance tooling for AI components. | S04 | "- Monitoring, evaluation and model governance tooling for the AI components." |
| FR-11 | must | Multi-channel ingestion | Ingest claim documents from various sources. | S07.1 | "**FR-1 Multi-channel ingestion.** The solution shall ingest claim documents from the web portal, mobile app, monitored email inboxes and scanned paper batches, and associate every document with the correct claim number in ClaimsNet." |
| FR-12 | must | Document classification | Classify documents into Corvane's taxonomy. | S07.1 | "**FR-2 Document classification.** The solution shall classify each incoming document into Corvane's document taxonomy (currently 27 document types, to be provided after contract award) with a confidence score." |
| FR-13 | must | Data extraction | Extract key fields from claim documents. | S07.1 | "**FR-3 Data extraction.** The solution shall extract key fields from claim forms, police reports, repair estimates and invoices, including at minimum: policy number, incident date, incident location, vehicle registration (motor), third-party details, itemised amounts and totals." |
| FR-14 | must | Handle low-quality documents | Handle handwritten and low-quality images. | S07.1 | "**FR-4 Handwriting and image quality.** The solution shall handle handwritten claim forms and low-quality phone photographs of documents, and shall flag documents that cannot be read reliably rather than guessing." |
| FR-15 | must | Generate claim summary | Generate a plain-language summary of each claim. | S07.1 | "**FR-5 Claim summarisation.** The solution shall generate a plain-language summary of each claim (no more than 200 words) for the assigned adjuster, highlighting the incident, the parties involved, amounts claimed and any missing documents. Every factual statement in the summary must be traceable to a source document." |
| FR-16 | must | Triage and routing | Route claims based on complexity score. | S07.1 | "**FR-6 Triage and routing.** The solution shall assign each claim a complexity score and route it to the appropriate line-of-business queue and adjuster tier, using rules configurable by Corvane's claims operations team without vendor involvement." |
| FR-17 | must | Identify fraud indicators | Solution must identify potential fraud indicators. | S07.1 | "**FR-7 Fraud indicators.** The solution shall identify potential fraud indicators (for example, inconsistent dates, duplicate invoices across claims, altered documents) and refer flagged claims to SIU with an explanation." |
| FR-18 | must | Never automatically decline claims | Solution must not automatically decline or close claims. | S07.1 | "The solution must never automatically decline or close a claim." |
| FR-19 | must | Human review | Allow adjusters to review and correct AI-generated outputs. | S07.1 | "**FR-8 Human review.** Adjusters shall be able to accept, correct or reject every AI-generated classification, extracted field and summary. Corrections shall be captured and made available for model improvement." |
| FR-20 | must | Capture corrections for model improvement | Corrections must be captured and made available for model improvement. | S07.2 | "Corrections shall be captured and made available for model improvement." |
| FR-21 | must | Missing information requests | Draft requests for missing documents. | S07.1 | "**FR-9 Missing information requests.** Where mandatory documents are missing, the solution should draft a request to the customer for the adjuster to review and send." |
| FR-22 | must | Provide operational dashboards | Operational dashboards must cover specified metrics. | S07.2 | "The solution shall provide operational dashboards covering volumes, processing times, routing accuracy, extraction accuracy and adjuster override rates." |
| FR-23 | should | Explain routing decisions | Routing decisions must be explainable in business terms. | S07.2 | "Corvane's claims operations managers have also asked that every routing decision be explainable in business terms, so that when a customer or the regulator asks why a claim was handled in a certain way, a team leader can answer without involving IT." |
| FR-24 | could | Support Bahasa Malaysia | Support for Bahasa Malaysia documents is expected from the pilot. | S13 | "Many of our customers in Sabah and in the northern region correspond in Bahasa Malaysia, and a meaningful minority of documents (we estimate 10 to 15%) arrive in Chinese. Support for Bahasa Malaysia documents is expected from the pilot." |
| FR-25 | could | Chinese document support | Support for Chinese documents is welcome but not required. | S13 | "Many of our customers in Sabah and in the northern region correspond in Bahasa Malaysia, and a meaningful minority of documents (we estimate 10 to 15%) arrive in Chinese. Support for Bahasa Malaysia documents is expected from the pilot. If Chinese-language documents could also be handled, that would be welcome, although we recognise this may come later and it is not a condition of award." |
| NFR-01 | must | Cut manual document keying effort | Cut manual document keying effort by at least 60% within twelve months of go-live. | S03 | "Cut manual document keying effort by at least 60% within twelve months of go-live." |
| NFR-02 | should | Historical claim documents | Approximately 2.1 million documents from the last five years may be usable for training and evaluation. | S06 | "Roughly 9 TB of historical claim documents exist, of which approximately 2.1 million documents relate to claims closed in the last five years and may be usable for training and evaluation, subject to the data protection constraints in section 8." |
| NFR-03 | should | Two data centres | The Company operates two data centres in Malaysia. | S06 | "The Company operates two data centres in Malaysia (primary in Cyberjaya, secondary in Johor) and has a limited Microsoft Azure footprint (Southeast Asia region) used today only for email and collaboration tools." |
| NFR-04 | must | Single document processing time | Classification and extraction for a single document must complete within 30 seconds. | S08 | "**NFR-1 Performance.** Classification and extraction for a single document should complete within 30 seconds of receipt at the 95th percentile." |
| NFR-05 | must | Claim triage and routing availability | Triage and routing for a complete claim must be available in real time. | S08 | "Triage and routing for a complete claim should be available to the adjuster in real time once all FNOL documents are received." |
| NFR-06 | must | Daily claim throughput | The solution must sustain peak volumes of 2,500 claims per day. | S08 | "**NFR-2 Throughput.** The solution shall sustain peak volumes of 2,500 claims per day (approximately three times the daily average), as experienced during the year-end monsoon flooding season, without degradation beyond the targets in NFR-1." |
| NFR-07 | must | Business hour availability | The production service must achieve 99.5% availability during business hours. | S08 | "**NFR-3 Availability.** The production service shall achieve 99.5% availability during business hours (08:00 to 20:00, Monday to Saturday)." |
| NFR-08 | must | Planned maintenance outside business hours | Planned maintenance must be scheduled outside business hours. | S08 | "Planned maintenance must be scheduled outside these hours." |
| NFR-09 | must | Continued claim flow during AI unavailability | Claims must continue to flow into ClaimsNet using the existing manual process. | S08 | "**NFR-4 Resilience.** If the AI components are unavailable, claims must continue to flow into ClaimsNet using the existing manual process, with no loss of documents." |
| NFR-10 | should | Scalability for other lines of business | The architecture must allow other lines of business to be onboarded by Corvane staff without re-architecture. | S08 | "**NFR-5 Scalability.** The architecture should allow other lines of business and additional document types to be onboarded by Corvane staff without re-architecture." |
| NFR-11 | must | Adjuster-facing interface accessibility | Adjuster-facing interfaces must meet WCAG 2.1 AA standards. | S08 | "**NFR-6 Accessibility and usability.** Adjuster-facing interfaces shall meet WCAG 2.1 AA." |
| NFR-12 | must | Version control for models and prompts | All models, prompts, and configuration must be version-controlled. | S08 | "**NFR-7 Maintainability.** All models, prompts and configuration shall be version-controlled, and every production output shall be traceable to the model and configuration version that produced it." |
| NFR-13 | must | Delete working copies within 30 days | Working copies must be deleted within 30 days of claim closure. | S10.2 | "Working copies of documents held by the solution must be deleted within 30 days of claim closure." |
| NFR-14 | should | Accommodate SIU investigations | Solution must accommodate longer document retention for SIU investigations. | S10.2 | "Bidders should note that the same documents may be required for SIU investigations for considerably longer, and the solution design must accommodate this." |
| NFR-15 | should | Evaluate model quality | Bidders must explain how they will evaluate model quality. | S13 | "Bidders should explain how they will evaluate model quality before and after go-live, including how they will measure extraction accuracy, routing accuracy and summary faithfulness, and how they will detect drift once in production." |
| SEC-01 | must | Compliance with PDPA | Solution must comply with PDPA and other regulations. | S10.1 | "Corvane is regulated by Bank Negara Malaysia (BNM) and must comply with the Personal Data Protection Act 2010 (PDPA) as amended, BNM's Risk Management in Technology (RMiT) policy, and its own information security standards." |
| SEC-02 | must | Data residency within Malaysia | Customer data must be stored and processed in Corvane's Malaysian data centres. | S10.1 | "All customer personal data, claim documents and derived data (including extracted fields, embeddings and model outputs) must be stored and processed within Corvane's own Malaysian data centres." |
| SEC-03 | must | Minimize personal data exposure | Personal data must be minimally exposed and masked in adjuster-facing summaries. | S10.1 | "The solution shall minimise exposure of personal data, mask identity card numbers in all adjuster-facing summaries except where explicitly needed, and shall not use personal data for any purpose other than claims handling and the improvement of the claims models." |
| SEC-04 | must | Audit trail logging | AI outputs, human overrides, and routing decisions must be logged with timestamps and details. | S10.1 | "Every AI output, every human override, and every routing decision shall be logged with a timestamp, user or system identity, input references and the model version used. Audit logs shall be immutable and retained for seven years." |
| SEC-05 | must | Role-based access control | Access must be role-based, with specific permissions for SIU staff and claims managers. | S10.1 | "Access shall be role-based. SIU fraud flags shall be visible only to SIU staff and designated claims managers, not to all adjusters." |
| SEC-06 | must | Annual security testing | Solution must undergo independent penetration testing annually. | S10.1 | "The solution shall undergo independent penetration testing before go-live and annually thereafter. Findings rated high or critical must be remediated before go-live." |
| SEC-07 | must | Support model risk management | Bidder must support Corvane's model risk management process. | S10.1 | "The bidder shall support Corvane's model risk management process, including documentation of model purpose, training data, known limitations, evaluation results and bias testing across customer segments." |
| SEC-08 | must | Disclose third-party models | Third-party models must be disclosed, including licensing and hosting details. | S10.1 | "Where foundation models or large language models are used, the bidder shall disclose the model, its licence, where it is hosted, and confirm that no Corvane data is used to train third-party models." |
| SEC-09 | should | Technical architecture evaluation | Technical architecture, security and compliance is weighted 25%. | S14 | "Technical architecture, security and compliance \| 25%" |
| INT-01 | must | Use ClaimsNet | The solution must use ClaimsNet for claims management. | S06 | "Claims are managed in **ClaimsNet**, an in-house claims management system built on Java and an Oracle 12c database in 2011." |
| INT-02 | must | Limited SOAP web services | ClaimsNet exposes a limited set of SOAP web services. | S06 | "ClaimsNet exposes a limited set of SOAP web services; there is no REST API today, and the vendor team that built it has largely moved on." |
| INT-03 | must | Use IBM MQ | Policy data must be accessed through IBM MQ. | S06 | "Policy data sits in a mainframe-hosted policy administration system (PAS) that is accessed through a message queue integration layer (IBM MQ)." |
| INT-04 | must | Near real-time read access | Near real-time read access to policy coverage details is allowed. | S06 | "Read access to policy coverage details is possible in near real time; write access is not permitted for this project." |
| INT-05 | must | Use DMS | Documents must be stored in the document management system (DMS). | S06 | "Documents are stored in a document management system (DMS) on a network file share, with metadata held in ClaimsNet." |
| INT-06 | must | Use Active Directory | Identity must be managed through on-premise Active Directory. | S06 | "Identity is managed through on-premise Active Directory. All internal applications must use single sign-on." |
| INT-07 | should | Description of new interfaces | Bidders must describe how new interfaces will be built and maintained. | S09 | "Where new interfaces are required, the bidder shall describe how they will be built and who will maintain them." |
| INT-08 | should | Prefer not to modify ClaimsNet's core codebase | Corvane prefers not to modify ClaimsNet's core codebase. | S09 | "Corvane prefers not to modify ClaimsNet's core codebase; minor additions to its user interface are acceptable if delivered through its plugin framework." |
| INT-09 | must | Policy coverage lookups using existing IBM MQ | Policy coverage lookups must use the existing IBM MQ integration layer. | S09 | "**INT-2** Policy coverage lookups shall use the existing IBM MQ integration layer." |
| INT-10 | must | No writing to policy administration system | The solution must not write to the policy administration system. | S09 | "The solution shall not write to the policy administration system." |
| INT-11 | must | Working copies retention | Working copies of documents may be held only as needed for processing. | S09 | "The solution may hold working copies only for as long as needed for processing, subject to the retention rules in section 8." |
| INT-12 | must | User authentication through Active Directory | Users must be authenticated through Corvane's Active Directory using single sign-on. | S09 | "**INT-4** The solution shall authenticate users through Corvane's Active Directory using single sign-on." |
| INT-13 | should | Avoid new dependencies on nightly SFTP batch interfaces | Bidders should avoid designing new dependencies on the nightly SFTP batch interfaces. | S09 | "The nightly SFTP batch interfaces are expected to be retired within two years. Bidders should avoid designing new dependencies on them." |
| COM-01 | must | Understand and maintain solution | Corvane's data science team must be able to understand, maintain and retrain the solution. | S03 | "Corvane's own data science team (currently six people) must be able to understand, maintain and retrain the solution after handover." |
| COM-02 | must | Knowledge transfer and training | Provide knowledge transfer and training for Corvane's IT, data science and claims teams. | S04 | "- Knowledge transfer and training for Corvane's IT, data science and claims teams." |
| COM-03 | could | Assume 16-20 weeks for GPU infrastructure | Assume 16-20 weeks for GPU infrastructure procurement, delivery and installation. | S11 | "Corvane does not currently own GPU infrastructure in either data centre. Our infrastructure team estimates that procurement, delivery and installation of new server hardware typically takes 16 to 20 weeks from purchase order, and capital purchases above MYR 1 million require Board approval at its quarterly meeting. Bidders should describe their assumptions about compute infrastructure clearly." |
| COM-04 | must | Budget range | The budget must be between MYR 6.5 million and MYR 8 million. | S12 | "The indicative budget envelope for this workstream is **MYR 6.5 million to MYR 8 million** over the initial contract term (contract award to handover)," |
| COM-05 | must | Discovery and design fixed price | A fixed price for discovery and design must be provided. | S12 | "- A fixed price for discovery and design." |
| COM-06 | must | Pilot fixed or capped price | A fixed or capped price for the pilot must be provided. | S12 | "- A fixed or capped price for the pilot." |
| COM-07 | must | Rollout phases pricing | Rollout phases can be priced as time-and-materials or fixed price, with rate cards. | S12 | "- A time-and-materials or fixed price, at the bidder's option, for the rollout phases, with rate cards." |
| COM-08 | must | Annual licence and support costs | Annual licence and support costs for five years after handover must be provided. | S12 | "- Annual licence and support costs for five years after handover." |
| COM-09 | must | Infrastructure or hardware recommendations | Recommendations for infrastructure or hardware must be provided, with indicative costs. | S12 | "- Any infrastructure or hardware the bidder recommends Corvane procure, with indicative costs, shown separately." |
| COM-10 | must | Milestone-based payment | Payment must be milestone-based, with at least 15% linked to measurable outcomes. | S12 | "Payment will be milestone-based. Corvane expects at least 15% of the services fee to be linked to achievement of measurable outcomes, for example routing accuracy and keying effort reduction, measured after the pilot." |
| COM-11 | must | Intellectual property rights | All intellectual property in custom work products must vest in Corvane. | S12 | "Corvane's standard terms require that all intellectual property in custom work products, including prompts, configurations, fine-tuned model weights and evaluation datasets created specifically for Corvane, vest in Corvane." |
| COM-12 | should | Describe comparable implementations | Bidders must describe at least two comparable implementations. | S13 | "Bidders should describe at least two comparable implementations in insurance or financial services, preferably in Southeast Asia, with client references." |
| COM-13 | should | Delivery lead and solution architect | A named delivery lead and solution architect must remain on the engagement. | S13 | "The proposed team must include a named delivery lead and a named solution architect who will remain on the engagement through at least full motor rollout." |
| COM-14 | should | Blended onshore and offshore team | A blended onshore and offshore team is required. | S13 | "Corvane expects a blended onshore and offshore team; however, any personnel with access to production data must be based in Malaysia and hold appropriate security clearance as determined by Corvane." |
| COM-15 | should | Solution fit evaluation | Solution fit to functional and non-functional requirements is weighted 30%. | S14 | "Solution fit to functional and non-functional requirements \| 30%" |
| COM-16 | should | Delivery approach evaluation | Delivery approach, timeline realism and team is weighted 20%. | S14 | "Delivery approach, timeline realism and team \| 20%" |
| COM-17 | should | Commercial value evaluation | Commercial value and total cost of ownership is weighted 15%. | S14 | "Commercial value and total cost of ownership \| 15%" |
| COM-18 | should | Capability transfer evaluation | Capability transfer and ongoing support is weighted 10%. | S14 | "Capability transfer and ongoing support \| 10%" |
| COM-19 | must | Electronic submission | Proposals must be submitted electronically. | S15 | "Proposals must be submitted electronically to the procurement portal by the due date stated above. Late submissions will not be considered." |
| COM-20 | should | Executive summary length | Executive summary must be no more than two pages. | S15 | "Proposals should contain:  1. An executive summary of no more than two pages." |
| COM-21 | should | Requirements compliance matrix | Compliance matrix must respond to every requirement. | S15 | "2. A requirements compliance matrix responding to every FR, NFR, INT and SEC requirement." |
| COM-22 | should | Solution architecture | Solution architecture must include deployment diagram. | S15 | "3. Solution architecture, including a deployment diagram showing where every component runs and where data is stored and processed." |
| COM-23 | should | Delivery plan and milestones | Delivery plan and milestones must be included. | S15 | "4. Delivery plan and milestones, with key assumptions and dependencies on Corvane." |
| COM-24 | should | Team structure and CVs | Team structure and CVs must be provided. | S15 | "5. Team structure and CVs of named personnel." |
| COM-25 | should | Commercial proposal | Commercial proposal must be in a separate document. | S15 | "6. Commercial proposal, in a separate document." |
| COM-26 | should | Risks and mitigations | Risks and proposed mitigations must be included. | S15 | "7. Risks and proposed mitigations." |
| COM-27 | should | Proposal length | Proposal main body must not exceed 40 pages. | S15 | "The main body of the proposal should not exceed 40 pages excluding appendices." |
| COM-28 | should | Clarification questions submission | Clarification questions must be submitted by 5 February 2027. | S15 | "Clarification questions must be submitted in writing through the procurement portal by 5 February 2027; Corvane will publish anonymised answers to all bidders by 12 February 2027." |
| TL-01 | must | Full rollout by 30 September 2027 | Full motor rollout must be completed by 30 September 2027. | S11 | "Full motor rollout, all offices \| 30 September 2027" |
| TL-02 | must | Home, travel and small-commercial lines live by 31 January 2028 | Home, travel and small-commercial lines must be live by 31 January 2028. | S11 | "Home, travel and small-commercial lines live \| 31 January 2028" |
| TL-03 | must | Handover to support by 31 March 2028 | Handover to Corvane support must be completed by 31 March 2028. | S11 | "Handover to Corvane support \| 31 March 2028" |
| TL-04 | must | Pilot go-live fixed | Pilot go-live date is fixed at 30 June 2027. | S11 | "The pilot go-live date of 30 June 2027 is fixed and is linked to a commitment made to the Board. Bidders proposing a later pilot date will need to provide an exceptionally strong justification." |

## Solution approach (14)

### 1. Develop a claims processing platform that integrates with ClaimsNet, DMS, and Active Directory, ensuring no core codebase modifications.

- **Addresses:** FR-01, FR-02, FR-05, FR-06, FR-07, FR-08, FR-10, FR-11, FR-12, FR-13, FR-14, FR-15, FR-16, FR-17, FR-18, FR-19, FR-20, FR-21, FR-22, NFR-01, NFR-04, NFR-05, NFR-06, NFR-07, NFR-08, NFR-09, NFR-11, NFR-12, NFR-13, SEC-01, SEC-02, SEC-03, SEC-04, SEC-05, SEC-06, SEC-07, SEC-08, INT-01, INT-02, INT-03, INT-04, INT-05, INT-06, INT-09, INT-10, INT-11, INT-12, COM-01, COM-02, COM-04, COM-05, COM-06, COM-07, COM-08, COM-09, COM-10, COM-11, COM-19, TL-01, TL-02, TL-03, TL-04
- **Components:** ClaimsNet SOAP adapter, Document management system (DMS) integration, Active Directory authentication, AI processing engine, Triage and routing system, Fraud detection module, Claim summary generator, Data extraction service, Low-quality document handling, User interface, Audit logging, Version control system, Model risk management tool, Security compliance module, Monitoring and evaluation dashboard, Legacy integration interfaces, User training and support, Milestone-based payment structure, Commercial support and maintenance plan, Blended onshore and offshore team, Solution fit evaluation, Commercial value assessment, Risk management plan, Electronic submission process, Compliance with PDPA and data residency, Near real-time policy coverage lookup, Document classification and data extraction, Claim triage and routing, Fraud indicator flagging, Adjuster-facing AI outputs, Missing information requests, Operational dashboards, Claim summary generation, Claim document handling, User authentication through Active Directory, Audit trail logging, Role-based access control, Annual security testing, Support for model risk management, Disclosure of third-party models, Technical architecture evaluation, Support for SIU investigations, Model quality evaluation, Compliance with WCAG 2.1 AA, Scalability for other lines of business, Version control for models and prompts, Delete working copies within 30 days, Claim triage and routing availability, Daily claim throughput, Business hour availability, Planned maintenance outside business hours, Continued claim flow during AI unavailability, Pilot and rollout phases pricing, Annual licence and support costs, Infrastructure recommendations, Discovery and design fixed price, Pilot fixed or capped price, Electronic submission, Knowledge transfer and training, Commercial proposal, Risks and mitigations, Solution architecture, Delivery plan and milestones, Team structure and CVs, Clarification questions submission, Full rollout by 30 September 2027, Home, travel and small-commercial lines live by 31 January 2028, Handover to support by 31 March 2028, Pilot go-live fixed price
- **Rationale:** This approach respects the constraints and ensures compliance with the client's requirements.

### 2. Provide a concise claim summary for adjusters.

- **Addresses:** FR-03
- **Components:** Claim summary generator, Natural language processing (NLP) engine, Data aggregation service
- **Rationale:** This feature will help adjusters quickly understand the claim context and make informed decisions.

### 3. Implement a fraud detection system that flags potential fraud cases.

- **Addresses:** FR-04
- **Components:** Fraud detection module, Machine learning model, Rule-based engine
- **Rationale:** This system will help in early detection and prevention of fraudulent claims.

### 4. Generate a claim summary to provide a quick overview to adjusters.

- **Addresses:** FR-15
- **Components:** Claim summary generator, NLP engine, Data aggregation service
- **Rationale:** This will streamline the claims processing workflow and improve adjuster efficiency.

### 5. Triage and route claims based on predefined criteria and flag potential fraud cases.

- **Addresses:** FR-16, FR-17
- **Components:** Triage and routing system, Fraud detection module, Rule-based engine
- **Rationale:** This ensures efficient claim handling and early fraud detection.

### 6. Ensure that no claims are automatically declined without human review.

- **Addresses:** FR-18
- **Components:** Claim review system, Human review interface
- **Rationale:** This prevents unjustified claim rejections and maintains customer trust.

### 7. Provide a human review interface for claims.

- **Addresses:** FR-19
- **Components:** Human review interface, Claim review system
- **Rationale:** This ensures that all claims are reviewed by a human before final processing.

### 8. Capture corrections for model improvement during the review process.

- **Addresses:** FR-20
- **Components:** Correction capture system, Model training pipeline
- **Rationale:** This will continuously improve the AI models and their accuracy.

### 9. Request missing information from claimants when necessary.

- **Addresses:** FR-21
- **Components:** Missing information request system, Claimant communication module
- **Rationale:** This ensures that all claims have the necessary information for processing.

### 10. Provide operational dashboards for monitoring claim processing and AI performance.

- **Addresses:** FR-22
- **Components:** Operational dashboards, Performance monitoring system
- **Rationale:** This will help in real-time monitoring and performance optimization.

### 11. Ensure compliance with PDPA, data residency, and other security and compliance requirements.

- **Addresses:** SEC-01, SEC-02, SEC-03, SEC-04, SEC-05, SEC-06, SEC-07, SEC-08
- **Components:** Data residency enforcement, PDPA compliance module, Audit logging, Role-based access control, Annual security testing, Model risk management tool, Third-party model disclosure
- **Rationale:** This will protect sensitive data and ensure legal and regulatory compliance.

### 12. Integrate with ClaimsNet, DMS, IBM MQ, Active Directory, and other legacy systems without modifying core codebases.

- **Addresses:** INT-01, INT-02, INT-03, INT-04, INT-05, INT-06, INT-09, INT-10, INT-11, INT-12
- **Components:** ClaimsNet SOAP adapter, DMS integration, IBM MQ integration, Active Directory authentication, Legacy system interfaces
- **Rationale:** This approach respects the client's constraints and ensures seamless integration.

### 13. Ensure the solution is maintainable, scalable, and can be supported over the long term.

- **Addresses:** COM-01, COM-02, COM-04, COM-05, COM-06, COM-07, COM-08, COM-09, COM-10, COM-11, COM-19
- **Components:** Version control system, Model training pipeline, Support and maintenance plan, Infrastructure recommendations, Discovery and design fixed price, Pilot fixed or capped price, Rollout phases pricing, Annual licence and support costs, Milestone-based payment structure, Electronic submission process
- **Rationale:** This will ensure the solution remains relevant and effective over time.

### 14. Deliver the solution by the specified timelines and phases.

- **Addresses:** TL-01, TL-02, TL-03, TL-04
- **Components:** Project management plan, Milestone-based delivery, Pilot and rollout phases, Handover to support
- **Rationale:** This will ensure the project is completed on time and within the defined phases.

## Risks (6)

| ID | Category | Title | L | I | Mitigation | Related |
|---|---|---|---|---|---|---|
| R-01 | requirement_conflict | **Fixed pilot date conflicts with hardware procurement timeline** - The fixed pilot go-live date of 30 June 2027 conflicts with the 16-20 week hardware procurement timeline, which may not be completed by the required date. | high | high | Agree an interim hosting option for the pilot, or re-baseline the date at contract award. | TL-01, INT-11 |
| R-02 | ambiguity | **Ambiguity in 'near real-time' data processing** - The requirement for near real-time data processing is vague and could lead to disputes over what constitutes 'near real-time'. | medium | medium | Clarify the definition of 'near real-time' with the client and document the agreed definition in the contract. | INT-04 |
| R-03 | security_compliance | **Security compliance with PDPA and data residency** - Ensuring compliance with PDPA and data residency within Malaysia while minimizing personal data exposure is complex and may introduce significant risks. | high | high | Conduct a detailed data protection impact assessment and ensure regular audits to maintain compliance. | SEC-02, SEC-03, SEC-04 |
| R-04 | delivery | **Risk of late hardware procurement** - The risk of late hardware procurement could delay the pilot and full rollout, impacting the project timeline. | high | high | Develop a contingency plan for hardware procurement and include it in the risk management plan. | INT-11 |
| R-05 | ambiguity | **Ambiguity in 'should' requirements** - The 'should' requirements, such as supporting Bahasa Malaysia and Chinese document support, are not clearly defined and could lead to disputes. | medium | medium | Clarify the scope and expected outcomes of these requirements with the client. | FR-24, FR-25 |
| R-06 | commercial | **Risk of exceeding budget** - The budget range of MYR 6.5 million to MYR 8 million may be underestimated, and the risk of exceeding this budget is high. | medium | high | Perform a detailed cost analysis and include a contingency reserve in the budget. | COM-04 |

## Assumptions

- ClaimsNet's core codebase will not be modified. _(The client has explicitly stated that no core codebase modifications are allowed.)_
- The solution will leverage existing interfaces and avoid new dependencies on nightly SFTP batch interfaces. _(This minimizes the risk and complexity of the solution.)_
- The solution will be designed to handle low-quality documents efficiently. _(This ensures the system can process a wide range of document types and quality levels.)_
- The solution will be version-controlled and traceable to ensure maintainability and compliance with regulatory requirements. _(This will facilitate model updates and ensure compliance with data protection regulations.)_
- The solution will be scalable to accommodate other lines of business and additional document types. _(This ensures the solution can be extended to support future business needs.)_

## Open questions for the client

- What is the target time for claim assignment to the correct adjuster? _(The current time of 3.8 working days is stated, but no target is given.)_
- What is the expected reduction in document re-keying time? _(The current 40% time spent on re-keying is mentioned, but no target is provided.)_
- What is the desired customer satisfaction target? _(The current 64% satisfaction is stated, but no target is given.)_
- What is the definition of 'straightforward claims'? _(The term is used in the FNOL to adjuster assignment time requirement but is not defined.)_
- What is the target report generation time? _(The current pain is stated but no target time is provided.)_
- What are the specific lodgement channels? _(The number of lodgement channels is mentioned but not specified.)_
- What is the exact scope of 'knowledge transfer and training'? _(The requirement mentions knowledge transfer and training but does not specify the content or depth.)_
- What specific data protection constraints apply to the use of historical claim documents? _(The text mentions data protection constraints but does not specify what they are.)_
- What is the taxonomy of document types? _(The number of document types is mentioned but not the specific types.)_
- What specific metrics should the dashboards cover? _(The RFP mentions specific metrics but does not provide exact details.)_
- What is the exact process for handling missing documents? _(The RFP mentions drafting requests but does not specify the exact process.)_
- What is the target model and configuration version traceability? _(The requirement states that outputs must be traceable to the model and configuration version, but does not specify the level of detail or method of traceability.)_
- What is the process for obtaining prior approval for using public cloud services? _(The RFP mentions a typical six to nine-month process, but no detailed steps or documentation are provided.)_
- What is the justification for the fixed pilot go-live date? _(The RFP states that a later date requires exceptionally strong justification, but no specific justification is provided.)_
- What are the specific measurable outcomes for the payment milestones? _(The RFP mentions measurable outcomes but does not specify what they are.)_
- What is the exact definition of 'comparable implementations'? _(The term 'comparable implementations' is not defined.)_
- What is the exact definition of 'full motor rollout'? _(The term 'full motor rollout' is not defined.)_
- What is the exact definition of 'drift' in the context of model quality evaluation? _(The term 'drift' is not defined.)_
- What is the exact definition of 'extraction accuracy', 'routing accuracy', and 'summary faithfulness'? _(The terms 'extraction accuracy', 'routing accuracy', and 'summary faithfulness' are not defined.)_
- What is the exact definition of 'pilot' in the context of document support? _(The term 'pilot' is not defined.)_
- What is the exact definition of 'near real-time' data processing? _(To avoid disputes and ensure clear expectations.)_
- What are the specific requirements for supporting Bahasa Malaysia and Chinese document support? _(To clarify the scope and expected outcomes.)_

## Critic history

- Pass 0: FAIL - 6 issue(s), 1 blocking
  - [high] numbered_coverage -> extract_requirements: RFP requirement FR-7 (section S07.1) was not extracted.
  - [medium] llm_review -> extract_requirements: FR-03 and FR-04 are both categorized as 'should' but seem to be closely related. Consider prioritizing one over the other or clarifying their distinct importance.
  - [medium] llm_review -> design_approach: The approach mentions integrating with ClaimsNet, IBM MQ, DMS, and Active Directory, but does not explicitly state that no modifications to ClaimsNet's core codebase will be made, which is a stated constraint (INT-08).
  - [low] llm_review -> analyze_risks: There are multiple risks related to the 'explain routing decisions' requirement (FR-21) that are not addressed in the risk register. Consider adding these to the risk register for better clarity.
  - [medium] llm_review -> extract_requirements: FR-22 and FR-23 are both marked as 'could' but seem to be redundant. Consider removing one of them or clarifying their distinct importance.
  - [medium] llm_review -> analyze_risks: There is a potential tension between the requirement to minimize personal data exposure (NFR-03) and the requirement to retain working copies (NFR-13). This tension is not addressed in the risk register. Consider adding this to the risk register.
- Pass 1: FAIL - 6 issue(s), 1 blocking
  - [high] must_coverage -> design_approach: No approach items produced.
  - [medium] llm_review -> extract_requirements: FR-12 and FR-13 are redundant as they both cover document classification and data extraction. Consider consolidating these into a single requirement.
  - [medium] llm_review -> extract_requirements: FR-16 and FR-17 are essentially the same, with slight variations. Consider consolidating them into a single requirement to avoid redundancy.
  - [medium] llm_review -> design_approach: The approach proposes modifying ClaimsNet's core codebase, which violates the constraint in INT-08. Clarify that the solution will not modify the core codebase of ClaimsNet.
  - [medium] llm_review -> analyze_risks: There is a tension between the requirement for a fixed pilot date (TL-01) and the risk of late hardware procurement (R-04). This should be explicitly addressed in the risk register.
  - [low] llm_review -> analyze_risks: R-05 mentions ambiguity in 'should' requirements but does not specify which 'should' requirements are ambiguous. Provide more detail to make this risk actionable.
- Pass 2: PASS - 5 issue(s), 0 blocking
  - [medium] llm_review -> extract_requirements: FR-03 and FR-15 are redundant as they both describe the same functionality of generating a claim summary. Consider consolidating these into a single requirement.
  - [medium] llm_review -> design_approach: The approach for FR-18 (Ensure that no claims are automatically declined without human review) violates the constraint in INT-10 (No writing to policy administration system) by potentially requiring interaction with the policy administration system during the review process.
  - [medium] llm_review -> analyze_risks: There is a tension between the requirement to provide near real-time policy coverage lookups (INT-09) and the constraint of no writing to the policy administration system (INT-10). This risk is not captured in the risk register.
  - [low] llm_review -> extract_requirements: FR-24 and FR-25 are marked as 'could' but are listed under 'must' priority. Consider adjusting the priority or category to match the actual intent.
  - [low] llm_review -> analyze_risks: R-05 mentions ambiguity in 'should' requirements but does not specify which 'should' requirements are ambiguous. This feedback should be more specific.

## Warnings

- architect step failed: [design_approach] output cut off at 2048 tokens
- architect did not return a final approach

## Run metadata

- Prompt versions: extract_requirements@1.1.0, design_approach@1.0.0, analyze_risks@1.0.0, critic@1.0.0, executive_summary@1.0.0
- LLM calls: 46, prompt tokens: 53539, completion tokens: 20214, model latency: 4364.9s, cost: $0.0000
- Wall time: 4367.1s
