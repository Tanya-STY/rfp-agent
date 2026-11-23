# Demo script (3–5 minutes)

**Recorded version:**
- **Video:** [watch on Google Drive](https://drive.google.com/file/d/1wF3rRDvgbwYvxeMZcEHbdhiGIwB3ORNd/view?usp=sharing), narrated by me. The file is kept out of git because of its size.
- A captioned walkthrough is in `demo/demo_walkthrough.pdf`.

The script below is for presenting it live.

**Setup before the call:**
- Ollama is running, both models are pulled, and the dashboard is open: `streamlit run app/dashboard.py`.
- Pre-run the main RFP so its results are ready: a live run takes ~14 min.
- Use the council RFQ (~2.5 min) for the live run.

---

### 0:00 – 0:30 · The problem

> "A bid team gets a 30-page RFP and has a few days to decide whether to bid and how. The slow, error-prone part is the first read: pulling out every obligation, spotting the contradictions, and knowing what to ask the client. This agent does that first read on a laptop, so confidential RFPs never leave the machine."

### 0:30 – 1:30 · Run it (Run tab)

- Pick `evals/rfps/rfp_adversarial_council.md` and click **Analyse RFP**. While it runs, point at the live log:
  - "Ingest splits the RFP into sections and builds a small search index."
  - "Extraction runs per batch of sections. Every requirement must come with a word-for-word quote, which code checks against the RFP."
  - "The architect designs per workstream with a bounded search tool. The risk analyst gets passages retrieved by code plus a checklist of classic RFP clashes."
  - "The critic checks coverage and grounding in code. If something important is wrong, it sends that one agent back to fix it."
- If it is slow, switch to the pre-computed run.

### 1:30 – 2:45 · The result (Results tab)

- **The warning banner:**
  > "This RFP contains a hidden instruction telling AI tools to make 'Northgate Analytics' a mandatory supplier. In the first version, my pipeline obeyed it. Now it's removed before any model sees it and raised as a question for a human."
- **Requirements table:** filter to `must` and point at the quote column.
  > "Every line is traceable to the exact RFP sentence. Priority comes from the RFP's own wording: shall means must, should means should."
- **Risks:**
  > "It found that R5 (host on the Council's own servers) contradicts R7 (supplier-hosted SaaS). That's the question a bid manager needs before pricing."
- **Open questions:** "Things the client must clarify: no timeline, no budget."

### 2:45 – 3:45 · How I know it works (Evaluation tab)

- Open `ba-main` (before/after), then `reviewed-main` (scored against the reviewed gold set):
  > "I hand-labelled the obligations in each test RFP. Scoring is deterministic: a prediction matches when its quote overlaps the labelled sentence."
- Before/after:
  > "Strict recall went from 84 to 93% on the main RFP, and 92 to 100% on two RFPs I wrote *before* fixing anything, so I wasn't tuning to the test. Precision stayed at 100%."
- Honesty point:
  > "I also built an LLM judge and calibrated it against my own labels. It agreed with me only half the time, so I don't use its scores for decisions. That's why the headline metrics are all computed in code."

### 3:45 – 4:30 · Cost and observability (Observability tab)

- Chart: "Where the time and tokens go: design is the biggest cost, and it's the next thing I'd optimise."
- Cost cards:
  > "$0 locally. The same run would be about 2 cents on Claude Haiku, and under a dollar on Opus, so a hosted option is cheap if the client allows it."
- Mention: "Every model call is also exported over OpenTelemetry, so the same traces open in Phoenix."

### 4:30 – 5:00 · Close

> "The design choice throughout: let the small model do the reading and judging, and let code do everything that must be exactly right: ids, quotes, priorities, coverage, the injection guard. Next steps are real RFPs, a stronger judge, and halving the design time."

---

**Likely follow-up questions:**
- **Why not one big prompt?** A 7B model loses focus and truncates; batching and per-workstream design fixed both (F3, F6, F13).
- **Why local?** Confidentiality, and $0. The provider switch makes hosted a config change.
- **What breaks it?** Scanned PDFs; injections worded differently from the guard's patterns; clash types not on the checklist. Free text the model writes (approach, risks) is not quote-checked: it once invented a pilot date of "October 15, 2024", so dates in the approach are now checked against the RFP in code.
- **Live change ideas:**
  - add a checklist pattern in `risk_analyst.conflict_candidates`
  - add a modal word to `_MODALS`
  - change `RFP_CHAT_MODEL`
