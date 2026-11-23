# RFP Solution Summary - rfp_synthetic_main.md

_Run `eval-20261122-204928-1` - model `qwen2.5:7b` - critic passed after 1 revision(s)_

## Executive summary

The client seeks a claims processing platform to reduce FNOL to adjuster assignment time and misrouted claims percentage. The proposed solution includes document ingestion, classification, extraction, triage, and AI-driven fraud detection, with operational dashboards for monitoring KPIs. Key risks include meeting the deadline while ensuring adequate lead time, achieving security compliance particularly regarding data residency, avoiding new dependencies during integration, securing board approval for large purchases, and managing data deletion vs retention policies.

## Requirements (82)

| ID | Priority | Title | Description | Source | Quote |
|---|---|---|---|---|---|
| FR-01 | must | Reduce FNOL to adjuster assignment time | Reduce average time from FNOL to correct adjuster assignment under 4 working hours. | S03 | "Reduce the average time from FNOL to correct adjuster assignment from 3.8 working days to under 4 working hours for straightforward claims." |
| FR-02 | must | Reduce misrouted claims percentage | Reduce misrouted claims from 22% to below 5%. | S03 | "Reduce misrouted claims from 22% to below 5%." |
| FR-03 | must | Provide concise claim summary | Give adjusters a concise, trustworthy summary of each claim. | S03 | "Give adjusters a concise, trustworthy summary of each claim so they can start assessment without opening every attachment." |
| FR-04 | must | Detect potential fraud | Improve early detection of potentially fraudulent claims by surfacing anomalies to SIU. | S03 | "Improve early detection of potentially fraudulent claims by surfacing anomalies to the Special Investigations Unit (SIU), without automatically declining any claim." |
| FR-05 | must | Ingest claim documents | Ingestion of claim documents from all four lodgement channels is in scope. | S04 | "- Ingestion of claim documents from all four lodgement channels." |
| FR-06 | must | Document classification and extraction | Document classification, data extraction and claim summarisation is in scope. | S04 | "- Document classification, data extraction and claim summarisation." |
| FR-07 | must | Triage claims | Triage: complexity scoring, line-of-business routing and adjuster queue assignment is in scope. | S04 | "- Triage: complexity scoring, line-of-business routing and adjuster queue assignment." |
| FR-08 | must | Fraud indicator flagging | Fraud-indicator flagging for referral to SIU is in scope. | S04 | "- Fraud-indicator flagging for referral to SIU." |
| FR-09 | must | Adjuster-facing AI outputs view | Provide an adjuster-facing view of the AI outputs. | S04 | "- An adjuster-facing view of the AI outputs (see section 6 regarding where this must live)." |
| FR-10 | must | AI monitoring and evaluation tooling | Provide monitoring, evaluation and model governance tooling for AI components. | S04 | "- Monitoring, evaluation and model governance tooling for the AI components." |
| FR-11 | must | Ingest claim documents from the web portal, mobile | The solution shall ingest claim documents from the web portal, mobile app, monitored email inboxes and scanned paper batches, and associate every document with the correct claim number in ClaimsNet. | S07.1 | "The solution shall ingest claim documents from the web portal, mobile app, monitored email inboxes and scanned paper batches, and associate every document with the correct claim number in ClaimsNet." |
| FR-12 | must | Document classification | Classify incoming documents into Corvane's taxonomy. | S07.1 | "The solution shall classify each incoming document into Corvane's document taxonomy (currently 27 document types, to be provided after contract award) with a confidence score." |
| FR-13 | must | Data extraction | Extract key fields from various claim documents. | S07.1 | "The solution shall extract key fields from claim forms, police reports, repair estimates and invoices, including at minimum: policy number, incident date, incident location, vehicle registration (motor), third-party details, itemised amounts and totals." |
| FR-14 | must | Handle low-quality documents | Handle handwritten claims and low-quality images. | S07.1 | "The solution shall handle handwritten claim forms and low-quality phone photographs of documents, and shall flag documents that cannot be read reliably rather than guessing." |
| FR-15 | must | Generate claim summary | Generate a plain-language summary for each claim. | S07.1 | "The solution shall generate a plain-language summary of each claim (no more than 200 words) for the assigned adjuster, highlighting the incident, the parties involved, amounts claimed and any missing documents." |
| FR-16 | must | Every factual statement in the summary must be | Every factual statement in the summary must be traceable to a source document. | S07.1 | "Every factual statement in the summary must be traceable to a source document." |
| FR-17 | must | Assign complexity score | Route claims based on complexity score. | S07.1 | "The solution shall assign each claim a complexity score and route it to the appropriate line-of-business queue and adjuster tier, using rules configurable by Corvane's claims operations team without vendor involvement." |
| FR-18 | must | Identify fraud indicators | Identify potential fraud in claims. | S07.1 | "The solution shall identify potential fraud indicators (for example, inconsistent dates, duplicate invoices across claims, altered documents) and refer flagged claims to SIU with an explanation." |
| FR-19 | must | No automatic claim closure | Solution must not automatically close claims. | S07.1 | "The solution must never automatically decline or close a claim." |
| FR-20 | must | Allow human review | Adjusters can accept, correct or reject AI-generated outputs. | S07.1 | "Adjusters shall be able to accept, correct or reject every AI-generated classification, extracted field and summary." |
| FR-21 | must | AI-generated classification | The solution must generate AI classifications. Also covers: Extracted fields and summaries. | S07.2 | "AI-generated classification, extracted field and summary." |
| FR-22 | must | Capture corrections for model improvement | Corrections must be captured and made available for model improvement. | S07.2 | "Corrections shall be captured and made available for model improvement." |
| FR-23 | must | Draft missing info requests | Draft requests for missing documents from customers. Also covers: Draft missing information requests. | S07.1 | "Where mandatory documents are missing, the solution should draft a request to the customer for the adjuster to review and send." |
| FR-24 | must | Provide operational dashboards | The solution must provide operational dashboards covering specified metrics. | S07.2 | "**FR-10 Reporting.** The solution shall provide operational dashboards covering volumes, processing times, routing accuracy, extraction accuracy and adjuster override rates." |
| FR-25 | should | Appear inside ClaimsNet claim screen | The solution should appear within the ClaimsNet claim screen or be reachable from it in a single click with context loaded. | S07.2 | "Whatever the solution produces needs to appear inside the ClaimsNet claim screen that adjusters already work in, or at minimum be reachable from it in a single click with the claim context already loaded." |
| FR-26 | must | Explain routing decisions | Every routing decision must be explainable in business terms. | S07.2 | "Corvane's claims operations managers have also asked that every routing decision be explainable in business terms, so that when a customer or the regulator asks why a claim was handled in a certain way, a team leader can answer without involving IT." |
| FR-27 | should | Support Bahasa Malaysia documents | Bahasa Malaysia document support is expected from the pilot. | S13 | "Support for Bahasa Malaysia documents is expected from the pilot." |
| FR-28 | could | Optional support for Chinese documents | Chinese document support would be welcome but not required. | S13 | "If Chinese-language documents could also be handled, that would be welcome, although we recognise this may come later and it is not a condition of award." |
| NFR-01 | must | Cut manual document keying effort | Cut manual document keying effort by at least 60% within twelve months of go-live. | S03 | "Cut manual document keying effort by at least 60% within twelve months of go-live." |
| NFR-02 | must | Read access to policy coverage details | The solution must provide read access to policy coverage details. | S06 | "Read access to policy coverage details is possible in near real time; write access is not permitted for this project." |
| NFR-03 | should | Single document classification | Classification and extraction for a single document should complete within 30 seconds. | S08 | "**NFR-1 Performance.** Classification and extraction for a single document should complete within 30 seconds of receipt at the 95th percentile." |
| NFR-04 | should | Claim triage availability | Triage and routing for a complete claim should be available to the adjuster in real time once all FNOL documents are received. | S08 | "Triage and routing for a complete claim should be available to the adjuster in real time once all FNOL documents are received." |
| NFR-05 | must | Peak throughput | Sustain peak volumes of 2,500 claims per day without degradation beyond NFR-1 targets. | S08 | "**NFR-2 Throughput.** The solution shall sustain peak volumes of 2,500 claims per day (approximately three times the daily average), as experienced during the year-end monsoon flooding season, without degradation beyond the targets in NFR-1." |
| NFR-06 | must | 99.5% availability | Achieve 99.5% availability during business hours. | S08 | "The production service shall achieve 99.5% availability during business hours (08:00 to 20:00, Monday to Saturday)." |
| NFR-07 | must | Planned maintenance must be scheduled outside these hours | Planned maintenance must be scheduled outside these hours. | S08 | "Planned maintenance must be scheduled outside these hours." |
| NFR-08 | must | Resilience with manual fallback | Claims must continue to flow into ClaimsNet using the existing manual process if AI components are unavailable. | S08 | "**NFR-4 Resilience.** If the AI components are unavailable, claims must continue to flow into ClaimsNet using the existing manual process, with no loss of documents." |
| NFR-09 | should | Scalability for other lines of business | Architecture should allow onboarding of other lines of business and additional document types by Corvane staff without re-architecture. | S08 | "**NFR-5 Scalability.** The architecture should allow other lines of business and additional document types to be onboarded by Corvane staff without re-architecture." |
| NFR-10 | must | WCAG 2.1 AA compliance | Adjuster-facing interfaces shall meet WCAG 2.1 AA standards. | S08 | "Adjuster-facing interfaces shall meet WCAG 2.1 AA." |
| NFR-11 | must | Version control for models and prompts | All models, prompts, and configuration must be version-controlled, with traceability to production outputs. | S08 | "All models, prompts and configuration shall be version-controlled, and every production output shall be traceable to the model and configuration version that produced it." |
| NFR-12 | must | Delete working copies within 30 days | Working copies must be deleted within 30 days of claim closure. | S10.2 | "Working copies of documents held by the solution must be deleted within 30 days of claim closure." |
| NFR-13 | should | Accommodate SIU document requirements | Solution design must accommodate longer-term document retention for SIU investigations. | S10.2 | "Bidders should note that the same documents may be required for SIU investigations for considerably longer, and the solution design must accommodate this." |
| NFR-14 | should | Model quality evaluation before go-live | Bidders should explain how they will evaluate model quality before go-live. Also covers: Model quality evaluation after go-live; Measure extraction accuracy; Measure routing accuracy; Measure summary faithfulness; Detect model drift. | S13 | "Bidders should explain how they will evaluate model quality before and after go-live, including how they will measure extraction accuracy, routing accuracy and summary faithfulness, and how they will detect drift once in production." |
| NFR-15 | should | Run evaluations post-handover | Corvane's data science team should run model quality evaluations after handover. | S13 | "Corvane's data science team will want to run these evaluations themselves after handover." |
| SEC-01 | must | Use single sign-on | The solution must use single sign-on with on-premise Active Directory for identity management. | S06 | "All internal applications must use single sign-on." |
| SEC-02 | must | Data must be stored in Malaysia | Customer personal data must be stored within Corvane's Malaysian data centres. | S10.1 | "All customer personal data, claim documents and derived data (including extracted fields, embeddings and model outputs) must be stored and processed within Corvane's own Malaysian data centres." |
| SEC-03 | must | Minimize exposure of personal data | Claim documents' personal data shall be minimally exposed in adjuster-facing summaries. | S10.1 | "The solution shall minimise exposure of personal data, mask identity card numbers in all adjuster-facing summaries except where explicitly needed, and shall not use personal data for any purpose other than claims handling and the improvement of the claims models." |
| SEC-04 | must | Audit logs must be immutable | AI outputs, human overrides, and routing decisions must be logged with timestamps and user identities. | S10.1 | "Every AI output, every human override, and every routing decision shall be logged with a timestamp, user or system identity, input references and the model version used." |
| SEC-05 | must | Audit logs shall be immutable and retained for | Audit logs shall be immutable and retained for seven years. | S10.1 | "Audit logs shall be immutable and retained for seven years." |
| SEC-06 | must | Access shall be role-based | Access shall be role-based. | S10.1 | "Access shall be role-based." |
| SEC-07 | must | Role-based access control | Access to SIU fraud flags is restricted to SIU staff and designated claims managers. | S10.1 | "SIU fraud flags shall be visible only to SIU staff and designated claims managers, not to all adjusters." |
| SEC-08 | must | Annual security testing required | Solution must undergo independent penetration testing annually. | S10.1 | "The solution shall undergo independent penetration testing before go-live and annually thereafter." |
| SEC-09 | must | Findings rated high or critical must be remediated | Findings rated high or critical must be remediated before go-live. | S10.1 | "Findings rated high or critical must be remediated before go-live." |
| SEC-10 | must | Support model risk management process | Bidder must support Corvane's model risk management process documentation. | S10.1 | "**SEC-6 Model risk.** The bidder shall support Corvane's model risk management process, including documentation of model purpose, training data, known limitations, evaluation results and bias testing across customer segments." |
| SEC-11 | must | Disclose third-party models | Third-party models must be disclosed. | S10.2 | "Where foundation models or large language models are used, the bidder shall disclose the model, its licence, where it is hosted, and confirm that no Corvane data is used to train third-party models." |
| SEC-12 | must | Security clearance for production data | Personnel with access to production data must be based in Malaysia and have appropriate security clearance. | S13 | "any personnel with access to production data must be based in Malaysia and hold appropriate security clearance as determined by Corvane." |
| INT-01 | must | Integration with ClaimsNet SOAP services | Use existing SOAP services for integration where they exist; describe new interfaces if required. | S09 | "**INT-1** Integration with ClaimsNet shall use the existing SOAP services where they exist." |
| INT-02 | must | Where new interfaces are required, the bidder shall | Where new interfaces are required, the bidder shall describe how they will be built and who will maintain them. | S09 | "Where new interfaces are required, the bidder shall describe how they will be built and who will maintain them." |
| INT-03 | must | Policy coverage lookups shall use the existing IBM | **INT-2** Policy coverage lookups shall use the existing IBM MQ integration layer. | S09 | "**INT-2** Policy coverage lookups shall use the existing IBM MQ integration layer." |
| INT-04 | must | Policy coverage lookups via IBM MQ | Use existing IBM MQ integration layer for policy coverage lookups; do not write to policy administration system. | S09 | "The solution shall not write to the policy administration system." |
| INT-05 | must | Document storage in DMS | Store documents in existing DMS as the system of record; hold working copies only for processing. | S09 | "**INT-3** Documents shall continue to be stored in the existing DMS as the system of record." |
| INT-06 | must | User authentication through Active Directory | Authenticate users through Corvane's Active Directory using single sign-on. | S09 | "**INT-4** The solution shall authenticate users through Corvane's Active Directory using single sign-on." |
| INT-07 | should | Avoid new dependencies on nightly SFTP batch interfaces | Design should avoid new dependencies on nightly SFTP batch interfaces, which are expected to be retired within two years. | S09 | "The nightly SFTP batch interfaces are expected to be retired within two years." |
| INT-08 | should | Avoid designing new dependencies on them | Bidders should avoid designing new dependencies on them. | S09 | "Bidders should avoid designing new dependencies on them." |
| COM-01 | must | Build internal capability | Solution must be understandable, maintainable and retrainable by Corvane's own data science team after handover. | S03 | "Corvane's own data science team (currently six people) must be able to understand, maintain and retrain the solution after handover." |
| COM-02 | must | Knowledge transfer training | Provide knowledge transfer and training for Corvane's IT, data science and claims teams. | S04 | "- Knowledge transfer and training for Corvane's IT, data science and claims teams." |
| COM-03 | should | Assume no existing GPU infrastructure | Solution should assume no existing GPU infrastructure in data centres. | S11 | "Corvane does not currently own GPU infrastructure in either data centre." |
| COM-04 | should | Assume typical procurement time | Solution should assume a typical procurement and installation time of 16-20 weeks for new server hardware. | S11 | "infrastructure team estimates that procurement, delivery and installation of new server hardware typically takes 16 to 20 weeks from purchase order, and" |
| COM-05 | should | Assume Board approval for large purchases | Solution should assume capital purchases above MYR 1 million require quarterly Board approval. | S11 | "capital purchases above MYR 1 million require Board approval at its quarterly meeting." |
| COM-06 | must | Budget range | The budget must be between MYR 6.5 million to MYR 8 million. | S12 | "The indicative budget envelope for this workstream is **MYR 6.5 million to MYR 8 million** over the initial contract term (contract award to handover)" |
| COM-07 | must | Discovery and design fixed price | A fixed price must be provided for discovery and design. | S12 | "- A fixed price for discovery and design." |
| COM-08 | must | Pilot fixed or capped price | A fixed or capped price must be provided for the pilot phase. | S12 | "- A fixed or capped price for the pilot." |
| COM-09 | must | Rollout phases pricing option | The bidder may choose between time-and-materials or fixed price for rollout phases, with rate cards provided. | S12 | "- A time-and-materials or fixed price, at the bidder's option, for the rollout phases, with rate cards." |
| COM-10 | must | Annual licence and support costs | Annual licence and support costs must be provided for five years after handover. | S12 | "- Annual licence and support costs for five years after handover." |
| COM-11 | must | Hardware procurement recommendation | Any recommended infrastructure or hardware must be provided with indicative costs, shown separately. | S12 | "- Any infrastructure or hardware the bidder recommends Corvane procure, with indicative costs, shown separately." |
| COM-12 | should | Milestone-based payment | Payment should be milestone-based, with at least 15% linked to measurable outcomes. | S12 | "Corvane expects at least 15% of the services fee to be linked to achievement of measurable outcomes, for example routing accuracy and keying effort reduction, measured after the pilot." |
| COM-13 | must | Intellectual property rights | All intellectual property in custom work products must vest in Corvane. | S12 | "Corvane's standard terms require that all intellectual property in custom work products, including prompts, configurations, fine-tuned model weights and evaluation datasets created specifically for Corvane, vest in Corvane." |
| COM-14 | should | Describe comparable implementations | Bidders should describe at least two comparable implementations. | S13 | "Bidders should describe at least two comparable implementations in insurance or financial services, preferably in Southeast Asia, with client references." |
| COM-15 | must | Delivery lead and solution architect commitment | A named delivery lead and a named solution architect must remain on the engagement through full motor rollout. | S13 | "The proposed team must include a named delivery lead and a named solution architect who will remain on the engagement through at least full motor rollout." |
| COM-16 | should | Blended onshore/offshore team | A blended onshore and offshore team is expected, with some personnel based in Malaysia. | S13 | "Corvane expects a blended onshore and offshore team" |
| TL-01 | must | Full rollout by specified dates | Full rollout must be completed by given deadlines. | S11 | "Full motor rollout, all offices \| 30 September 2027 \| \| Home, travel and small-commercial lines live \| 31 January 2028" |
| TL-02 | must | Handover to support by March 2028 | Solution must be handed over to Corvane support by 31 March 2028. | S11 | "Handover to Corvane support \| 31 March 2028" |
| TL-03 | must | Pilot go-live fixed date | Pilot go-live by 30 June 2027 is mandatory. | S11 | "The pilot go-live date of 30 June 2027 is fixed and is linked to a commitment made to the Board." |

## Solution approach (39)

### 1. Develop a claims processing platform that integrates document ingestion, classification, extraction, triage, and AI-driven fraud detection.

- **Addresses:** FR-01, FR-02, FR-03, FR-04, FR-05, FR-06, FR-07, FR-08, FR-09, FR-10, FR-11, FR-12
- **Components:** Document Ingestion Service, AI Engine, Claim Summary Generator, Triage System, Fraud Detection Module, Data Extraction Pipeline, Configuration Interface, Monitoring Tool, Mobile and Web Portal Integration, Legacy API Adapter, Cloud Storage Solution, Natural Language Processing (NLP) Model, Machine Learning Models for Classification and Fraud Detection, Message Queue Infrastructure, API Gateway
- **Rationale:** This approach covers all must-priority requirements while leveraging modern technologies for efficiency and scalability.

### 2. Combine document ingestion from web portal, mobile app, email, and paper batches into a single component to avoid redundancy.

- **Addresses:** FR-05, FR-11
- **Components:** Unified Document Ingestion Service, Message Queue Infrastructure, API Gateway
- **Rationale:** This consolidation reduces complexity and ensures consistent data handling across all channels.

### 3. Develop a document ingestion service that extracts key fields from various claim documents, handling low-quality inputs and flagging unreadable ones.

- **Addresses:** FR-13, FR-14
- **Components:** Document ingestion workers, Low-quality document handler, IBM MQ adapter
- **Rationale:** Reuses existing IBM MQ for integration with the DMS, ensuring compatibility with legacy systems and data protection constraints.

### 4. Implement a summarization module that generates claim summaries based on extracted facts, ensuring all factual statements are verifiable.

- **Addresses:** FR-15, FR-16
- **Components:** Summarization engine, ClaimsNet API adapter
- **Rationale:** Uses existing metadata from ClaimsNet to maintain accuracy and avoid data duplication, aligning with the client's need for precision in claims processing.

### 5. Integrate a machine learning model to assign complexity scores to claims based on extracted fields.

- **Addresses:** FR-17
- **Components:** Complexity scoring model, IBM MQ listener
- **Rationale:** Leverages existing document taxonomy and IBM MQ for seamless data flow, ensuring the solution is scalable with minimal impact on legacy systems.

### 6. Deploy a fraud detection module that identifies potential fraudulent claims by analyzing extracted fields.

- **Addresses:** FR-18
- **Components:** Fraud detection model, Document metadata analysis
- **Rationale:** Uses existing document management system for data access, ensuring the solution is compliant with data protection regulations and legacy constraints.

### 7. Ensure no automatic claim closure; all decisions require human review.

- **Addresses:** FR-19
- **Components:** Human review workflow
- **Rationale:** Maintains control over claims closure process to ensure accuracy and compliance with internal policies.

### 8. Allow for manual corrections during the review process to improve model accuracy.

- **Addresses:** FR-20
- **Components:** Correction input interface
- **Rationale:** Facilitates continuous improvement of AI models through human feedback, enhancing overall system performance.

### 9. Automate claim classification using AI-generated labels based on extracted fields.

- **Addresses:** FR-21
- **Components:** AI-generated classification model
- **Rationale:** Enhances operational efficiency by reducing manual intervention in the claims processing workflow.

### 10. Capture corrections for model improvement and draft missing information requests to ensure completeness of claims data.

- **Addresses:** FR-22, FR-23
- **Components:** Correction capture module, Missing info request generator
- **Rationale:** Supports ongoing model training and ensures comprehensive claim records, aligning with client's need for continuous improvement.

### 11. Provide operational dashboards to monitor key performance indicators (KPIs) related to claims processing.

- **Addresses:** FR-24
- **Components:** Dashboards for KPIs
- **Rationale:** Enables real-time monitoring and analysis of claims data, supporting informed decision-making and process optimization.

### 12. Develop a routing decision explanation module that provides business-friendly explanations for claims processing decisions.

- **Addresses:** FR-26
- **Components:** -
- **Rationale:** This aligns with Corvane's need to explain routing decisions in business terms, ensuring adjusters and leadership can justify actions to customers or regulators.

### 13. Implement a load balancer and auto-scaling group to ensure peak throughput and 99.5% availability.

- **Addresses:** NFR-05
- **Components:** -
- **Rationale:** Automates scaling based on demand, ensuring performance without manual intervention.

### 14. Schedule maintenance during off-peak hours to minimize impact on service availability.

- **Addresses:** NFR-06, NFR-07
- **Components:** -
- **Rationale:** Ensures minimal disruption to users and critical operations.

### 15. Automate document ingestion from email and portal channels, ensuring read access to policy coverage details.

- **Addresses:** NFR-01, NFR-02
- **Components:** -
- **Rationale:** Reuses existing interfaces, avoiding changes to the core system the client wants untouched.

### 16. Implement a manual fallback mechanism for resilience in case of service failure.

- **Addresses:** NFR-08
- **Components:** -
- **Rationale:** Provides a reliable backup plan that can be manually triggered if needed.

### 17. Ensure WCAG 2.1 AA compliance, version control for models and prompts, and delete working copies within 30 days.

- **Addresses:** NFR-10, NFR-11, NFR-12
- **Components:** -
- **Rationale:** Meets accessibility standards and manages data lifecycle efficiently.

### 18. Implement a quality evaluation framework to model and run evaluations both pre-go-live and post-handover.

- **Addresses:** NFR-14, NFR-15
- **Components:** Evaluation engine, Pre-go-live scheduler, Post-handover monitor
- **Rationale:** Combines NFR-14 and NFR-15 into one component for efficiency, ensuring consistent evaluation processes throughout the project lifecycle.

### 19. Implement single sign-on (SSO) and role-based access control.

- **Addresses:** SEC-01, SEC-06
- **Components:** SSO provider, RBAC engine
- **Rationale:** SSO simplifies user authentication, while RBAC ensures secure data access based on roles.

### 20. Store data in a Malaysia-based cloud service to meet data residency requirements.

- **Addresses:** SEC-02
- **Components:** Cloud storage service
- **Rationale:** Complies with local regulations and minimizes latency for users in the region.

### 21. Minimize exposure of personal data through role-based access control and secure APIs.

- **Addresses:** SEC-03, SEC-07
- **Components:** RBAC engine, Secure API gateway
- **Rationale:** Reduces unauthorized access to sensitive information.

### 22. Ensure audit logs are immutable and retained for compliance purposes.

- **Addresses:** SEC-04, SEC-05
- **Components:** Immutable storage service, Audit log management tool
- **Rationale:** Maintains a record of all actions taken on the system for auditing and regulatory requirements.

### 23. Schedule annual security testing to identify and mitigate vulnerabilities.

- **Addresses:** SEC-08
- **Components:** Security testing service
- **Rationale:** Regularly assesses the security posture of the system to ensure compliance with best practices.

### 24. Remediate high or critical findings from security assessments promptly.

- **Addresses:** SEC-09
- **Components:** Automated remediation tool
- **Rationale:** Ensures that significant security issues are addressed in a timely manner to prevent breaches.

### 25. Support the model risk management process by documenting and monitoring models.

- **Addresses:** SEC-10
- **Components:** Model documentation system, Risk monitoring tool
- **Rationale:** Facilitates compliance with regulatory requirements for managing financial risks.

### 26. Disclose third-party models used in the system to relevant stakeholders.

- **Addresses:** SEC-11
- **Components:** Third-party model disclosure portal
- **Rationale:** Ensures transparency and accountability regarding the use of external models.

### 27. Ensure personnel handling production data have appropriate security clearances.

- **Addresses:** SEC-12
- **Components:** Security clearance management system
- **Rationale:** Protects sensitive information from unauthorized access by ensuring staff are vetted properly.

### 28. Implement integration with ClaimsNet SOAP services using existing API endpoints.

- **Addresses:** INT-01, INT-02
- **Components:** SOAP service client, API gateway
- **Rationale:** Reuses existing interfaces, avoiding changes to the core system the client wants untouched.

### 29. Utilize IBM MQ for policy coverage lookups and ensure compliance with existing integration patterns.

- **Addresses:** INT-03, INT-04
- **Components:** IBM MQ client, Message handler
- **Rationale:** Maintains consistency with current practices, reducing risk of errors or misconfigurations.

### 30. Integrate document storage into the DMS system following the client's data residency requirements.

- **Addresses:** INT-05
- **Components:** DMS API adapter, Document uploader
- **Rationale:** Ensures compliance with local data storage regulations and minimizes cross-border data transfer risks.

### 31. Authenticate users through Active Directory to ensure secure access control.

- **Addresses:** INT-06
- **Components:** AD connector, Authentication service
- **Rationale:** Leverages existing identity management systems for seamless user authentication and authorization.

### 32. Develop a detailed plan for building internal capability and knowledge transfer training.

- **Addresses:** FR-03
- **Components:** -
- **Rationale:** Addresses must-priority requirements COM-01 and COM-02, ensuring client's workforce is prepared.

### 33. Outline pricing options including discovery and design fixed price, pilot fixed or capped price, rollout phases with phased payments, annual licence and support costs.

- **Addresses:** COM-06, COM-07, COM-08, COM-09, COM-10
- **Components:** -
- **Rationale:** Provides comprehensive financial planning to fit the budget range and client's procurement processes.

### 34. Recommend hardware procurement options that align with the project needs and budget constraints.

- **Addresses:** COM-11
- **Components:** -
- **Rationale:** Ensures hardware recommendations are within budget and meet project requirements, addressing COM-11.

### 35. Define pricing options for discovery and design, pilot phases, rollout phases with phased payments, annual licence and support costs.

- **Addresses:** COM-06, COM-07, COM-08, COM-09, COM-10
- **Components:** -
- **Rationale:** Addresses must-priority requirements COM-06, COM-07, COM-08, COM-09, and COM-10.

### 36. Establish internal capability and provide training to transfer knowledge to the client's team.

- **Addresses:** COM-01, COM-02
- **Components:** -
- **Rationale:** Addresses must-priority requirements COM-01 and COM-02, ensuring readiness for implementation.

### 37. Define the intellectual property rights agreement to ensure all parties' interests are protected.

- **Addresses:** COM-13
- **Components:** -
- **Rationale:** Protects both the client and our company from potential legal issues related to IP ownership.

### 38. Nominate a dedicated delivery lead and solution architect, and outline their roles in ensuring project success.

- **Addresses:** COM-15, TL-01, TL-02
- **Components:** Project management tool, Regular status meetings
- **Rationale:** Ensures accountability and clear leadership for the project's timeline and milestones.

### 39. Schedule the pilot go-live date to align with the pre-defined fixed date, ensuring all necessary preparations are in place.

- **Addresses:** TL-03
- **Components:** -
- **Rationale:** Allows for thorough testing and validation before full-scale implementation.

## Risks (6)

| ID | Category | Title | L | I | Mitigation | Related |
|---|---|---|---|---|---|---|
| R-01 | requirement_conflict | **Deadline vs lead time** - The fixed pilot go-live date of 30 June 2027 conflicts with the hardware procurement timeline, which typically takes 16 to 20 weeks from purchase order. | high | high | Agree an interim approved hosting option for the pilot or re-baseline the date at contract award. | TL-03, SEC-02 |
| R-02 | requirement_conflict | **Deletion vs retention** - There is a potential conflict between NFR-12, which requires deleting working copies within 30 days, and NFR-13, which states that SIU document requirements may necessitate retaining certain documents for longer periods. | medium | medium | Clarify with the client how long working copies must be retained and ensure compliance with both NFR-12 and NFR-13. | NFR-12, NFR-13 |
| R-03 | ambiguity | **Ambiguity: Real-time targets** - The terms 'real time' in NFR-02 and NFR-04 are not quantified, which could lead to disputes over the system's performance. | medium | low | Define clear metrics for 'real time' in both requirements to avoid misunderstandings. | NFR-02, NFR-04 |
| R-04 | security_compliance | **Security compliance: Data residency** - The requirement that all customer data must be stored and processed within Corvane's Malaysian data centres (SEC-02) may conflict with the need for peak throughput and 99.5% availability, as local storage might limit performance. | medium | high | Evaluate the impact of data residency on system performance and explore potential solutions such as edge computing or hybrid cloud strategies. | SEC-02, NFR-05 |
| R-05 | integration | **Integration: Avoiding new dependencies** - The requirement to avoid new dependencies on nightly SFTP batch interfaces (INT-07 and INT-08) may conflict with the need for peak throughput, as manual fallback options could impact performance. | medium | high | Assess the feasibility of alternative integration methods that do not rely on SFTP interfaces and ensure they meet the required performance standards. | INT-07, INT-08 |
| R-06 | commercial | **Commercial: Board approval for large purchases** - The requirement to assume typical procurement time (COM-04) may conflict with the need for a fixed price pilot phase, as delays in obtaining Board approval could impact project timelines. | medium | high | Provide a detailed timeline that accounts for potential delays in obtaining Board approval and include contingency plans in the bid proposal. | COM-04, TL-03 |

## Assumptions

- The exact number of document types in Corvane's taxonomy will be provided after contract award. _(To ensure accurate classification, we need the complete taxonomy.)_
- Corvane's claims operations team can configure routing rules without vendor involvement. _(This allows for flexibility and local optimization of claim processing workflows.)_
- The document taxonomy will be provided after contract award. _(Ensures alignment with client's specific needs without premature assumptions.)_
- The complexity scoring and fraud detection models are third-party solutions. _(Allows for leveraging existing, proven technologies while maintaining compliance with data protection constraints.)_
- The team will include a named delivery lead and solution architect who will remain on the engagement through full motor rollout. _(Ensures continuity and alignment with Corvane's expectations for key personnel.)_
- Corvane's data science team will run evaluations after handover to measure model quality. _(Meets the client's need for ongoing quality assurance without duplicating effort.)_
- Off-peak hours are defined as 2 AM - 6 AM local time _(RFP does not specify exact off-peak hours, so we assume a common timeframe.)_
- Maintenance tasks can be automated using existing tools and scripts. _(Automation is assumed to reduce manual effort while maintaining compliance with the client's constraints.)_

## Open questions for the client

- What is the target time for claim assignment? _(The current average time (3.8 working days) is context, not a requirement.)_
- What are the specific document types that must be handled by the platform? _(While it mentions several document types, there's no explicit statement of what must be included in the solution.)_
- How should claims be classified and triaged? _(The method or criteria for classification and triage are not specified.)_
- What is the expected reduction in adjuster time spent on reading documents? _(While 40% of their time is mentioned, there's no target stated.)_
- How should customer satisfaction be improved according to the RFP? _(The current and desired levels of customer satisfaction are not quantified.)_
- What is the definition of 'straightforward claims'? _(The term 'straightforward claims' is not defined in the RFP.)_
- What are the data protection constraints in section 8? _(The quote mentions data protection constraints but does not specify them.)_
- What is the taxonomy of document types? _(The number of document types (27) is mentioned but not detailed.)_
- What specific metrics should the operational dashboards cover? _(The RFP mentions volumes, processing times, routing accuracy, extraction accuracy and adjuster override rates but does not specify these as requirements.)_
- What is the exact context for claims in ClaimsNet that must be loaded when accessing the solution? _(The RFP states that the solution should appear inside or be reachable from the ClaimsNet claim screen, but it does not provide details on what specific context needs to be loaded.)_
- What is the exact definition of 'degradation beyond NFR-1 targets'? _(The quote does not specify what constitutes degradation.)_
- What specific actions must be taken for high or critical findings from security testing? _(The quote mentions remediation but does not specify the exact steps.)_
- Is there a specific timeline for when the solution should undergo initial penetration testing? _(While it is mentioned that testing must be done before go-live, no specific date or time frame is provided.)_
- What is the definition of 'working copies'? _(The term 'working copies' is not defined in the RFP.)_
- What constitutes an 'exceptionally strong justification' for a later pilot date? _(The criteria for what qualifies as an exceptionally strong justification are not specified.)_
- What are the specific measurable outcomes for payment milestones? _(The RFP mentions measurable outcomes but does not specify what they are.)_
- What is the expected level of detail for client references? _(The RFP mentions providing client references but does not specify the required level of detail.)_
- How will 'drift' be defined and measured? _(While drift detection is mentioned, there is no clear definition or measurement criteria provided.)_
- How will the system handle data that needs to be retained for SIU investigations but must also be deleted within 30 days? _(To ensure compliance with both NFR-12 and NFR-13.)_
- What specific metrics should be used to define 'real time' in NFR-02 and NFR-04? _(To avoid disputes over the system's performance.)_

## Critic history

- Pass 0: FAIL - 6 issue(s), 1 blocking
  - [high] must_coverage -> design_approach: These must-priority requirements are not addressed by any approach item: COM-11. Add them to the relevant items.
  - [medium] llm_review -> extract_requirements: FR-12 and FR-13 are redundant as they both address document classification and extraction, with only minor differences in scope.
  - [medium] llm_review -> design_approach: The approach for FR-05 (Ingest claim documents) and FR-11 (Ingest claim documents from the web portal, mobile) should be combined into a single component to avoid redundancy.
  - [medium] llm_review -> analyze_risks: There is no risk related to the tension between NFR-06 (99.5% availability) and TL-02 (Full rollout by specified dates). This should be added to ensure both are considered.
  - [low] llm_review -> extract_requirements: FR-19 and FR-20 have similar content but different wording. Consider consolidating them for clarity.
  - [low] llm_review -> design_approach: The approach for NFR-14 (Model quality evaluation before go-live) and NFR-15 (Run evaluations post-handover) should be combined into a single component to avoid redundancy.
- Pass 1: PASS - 5 issue(s), 0 blocking
  - [medium] llm_review -> extract_requirements: FR-12 and FR-13 are redundant as they both address document classification, with only minor differences in scope.
  - [medium] llm_review -> design_approach: The approach violates the constraint of storing data in Malaysia (SEC-02) by proposing a cloud storage solution that may not be based in Malaysia.
  - [medium] llm_review -> analyze_risks: There is an obvious tension between NFR-05 (peak throughput) and SEC-08 (annual security testing), which could impact the system's availability. This risk should be explicitly addressed.
  - [low] llm_review -> extract_requirements: FR-26 is marked as 'must' but its title and description are incomplete, which could lead to misinterpretation.
  - [low] llm_review -> design_approach: The approach does not explicitly address the requirement of no automatic claim closure (FR-19), even though it mentions a human review workflow.

## Run metadata

- Prompt versions: extract_requirements@1.4.0, design_approach@2.0.0, analyze_risks@1.2.0, critic@1.0.0, executive_summary@1.0.0
- LLM calls: 48, prompt tokens: 61762, completion tokens: 21006, model latency: 865.5s, cost: $0.0000
- Wall time: 866.1s
