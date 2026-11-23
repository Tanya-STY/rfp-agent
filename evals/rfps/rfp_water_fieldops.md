# Request for Tender: Field Maintenance Knowledge Assistant

**Issuing body:** Ellery Basin Water Corporation ("Ellery Water", "the Corporation")
**Tender number:** EBW-T-2027-031
**Released:** 3 March 2027
**Closing:** 14 April 2027, 2:00 pm

---

## 1. Background

Ellery Water supplies drinking water and wastewater services to about 640,000 people across a regional catchment of 18,000 square kilometres. The Corporation maintains 41 treatment plants, 312 pump stations and roughly 9,500 km of pipe.

Maintenance is carried out by 260 field technicians working in crews of two or three. Technicians rely on a library of around 14,000 documents: equipment manuals from more than 90 manufacturers, standard operating procedures, safety data sheets and as-built drawings. Many manuals are scanned PDFs, some more than thirty years old. Finding the right page in the field is slow: in a 2026 time-and-motion study, technicians spent an average of 47 minutes per shift searching for information, and senior technicians reported fielding around twelve phone calls a day from junior staff.

Roughly a third of the senior workforce is expected to retire within five years. The Corporation wants to capture their knowledge before it leaves.

## 2. What we are buying

Ellery Water is seeking a supplier to deliver a knowledge assistant that field technicians can ask questions of, in plain English, and that answers from the Corporation's own documents. The assistant will also help technicians write up completed work orders.

The following are out of scope: asset investment planning, customer billing, and any control of plant equipment. The assistant must not issue commands to the SCADA system under any circumstances.

## 3. Functional requirements

**F1 Question answering.** The assistant shall answer technicians' questions using only the Corporation's approved document library and shall cite the document and page for every answer.

**F2 Refusal when unsure.** Where the library does not contain an answer, the assistant shall say so plainly rather than offering a best guess.

**F3 Safety-critical content.** For any question involving isolation, confined-space entry, chlorine handling or live electrical work, the assistant shall display the relevant safe work procedure in full, not a summary.

**F4 Work order write-up.** The assistant should draft the completion notes for a work order from a technician's spoken or typed description, for the technician to check and submit to the Maximo asset management system.

**F5 Knowledge capture.** The solution shall let nominated senior technicians record tips and workarounds, which are reviewed by a maintenance planner before being added to the library.

**F6 Feedback.** Technicians shall be able to flag any answer as wrong or unhelpful in no more than two taps.

Most of our sites have no mobile coverage. Pump stations in the eastern ranges in particular can be two hours' drive from the nearest signal, and crews are often there for a full day. A tool that only works with a connection will not be used.

Technicians wear gloves for most tasks, and some will want to use the assistant by voice.

## 4. Non-functional requirements

**N1 Response time.** Answers should be returned quickly enough that technicians do not abandon the tool.

**N2 Accuracy.** The supplier shall demonstrate, before go-live, that the assistant answers correctly on a test set of at least 300 questions agreed with Ellery Water, with an accuracy of at least 90%.

**N3 Devices.** The assistant shall run on the Corporation's standard ruggedised Android tablets (Samsung Galaxy Tab Active5).

**N4 Content updates.** New or revised documents shall be searchable by the assistant within two working days of being approved in the document library.

## 5. Integration

**I1** Work orders shall be read from and written to IBM Maximo 7.6 through its existing REST API.

**I2** The document library is held in SharePoint Online in the Corporation's Microsoft 365 tenant. The solution shall read documents from there and shall not keep an unmanaged copy elsewhere.

**I3** Users shall sign in with their existing Microsoft Entra ID accounts.

Integration with the GIS (Esri ArcGIS) to show nearby assets would be desirable but is not essential for the first release.

## 6. Security, privacy and records

Ellery Water is a state-owned corporation and is subject to the State Records Act and the state's information security framework.

**S1 Hosting.** The solution may use cloud services provided they are hosted in Australian data centres. Data shall not leave Australia.

**S2 Records.** Every question asked of the assistant, the answer given and the documents cited shall be retained as a public record for seven years.

**S3 Voice.** Voice recordings of technicians shall not be stored after transcription, under the Corporation's agreement with the technicians' union.

**S4 Access.** Contractors working for Ellery Water shall have access only to the documents relevant to their contract.

## 7. Delivery and commercial

The Corporation would like the assistant in the hands of a pilot group of 30 technicians by 1 July 2027, with full rollout by the end of 2027. The supplier shall provide a delivery plan showing how these dates will be met.

Under the Corporation's enterprise agreement, any new tool used by field staff requires twelve weeks of formal consultation with the union before it can be introduced. Consultation can begin only once the tool's design is settled.

The supplier shall provide a fixed price for the pilot and a per-user annual subscription price for rollout. The total contract value is not expected to exceed AUD 1.8 million over three years.

The supplier shall provide training for all field technicians, delivered at depots, and shall not rely on online self-paced training alone.

## 8. Evaluation

Tenders will be evaluated on: fit to requirements (40%), price (25%), delivery approach (20%) and supplier capability (15%).

## 9. How to respond

Responses shall be lodged through the state e-tendering portal. Responses should not exceed 30 pages. Questions must be submitted by 31 March 2027.
