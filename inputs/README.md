# inputs/

`rfp_synthetic_main.md` is a **synthetic stand-in** RFP (fictional insurer "Corvane Mutual
Assurance") written so the pipeline can be built and tested before the real brief arrives.
It is deliberately messy, the way real RFPs are:

- some requirements are numbered (FR-*, NFR-*, INT-*, SEC-*), others are implied in prose
  (e.g. adjusters refusing to switch screens -> UI must live inside ClaimsNet);
- one ambiguity: NFR-1 asks for triage "in real time" without defining it;
- one tension: a fixed 30 June 2027 pilot vs. SEC-1 (all inference on-prem, no public
  cloud without a 6-9 month approval) and a 16-20 week GPU procurement lead time;
  plus a softer one between 30-day deletion of working copies and longer SIU retention;
- a buried nice-to-have: Chinese-language document support (section 11).

The real brief will be dropped into this folder later. Any `.md`, `.txt`, `.pdf` or `.docx`
file works with no code change:

```bash
python -m rfp_agent run --input inputs/<file>
# or, if it is the only non-README file in the folder:
python -m rfp_agent run --input inputs
```
