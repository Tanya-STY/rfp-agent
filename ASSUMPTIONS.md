# Assumptions

What this build assumes about the brief, the user and the environment. If any of these
turn out wrong, the section named in brackets is what would change.

## About the brief

- **The real RFP brief has not arrived.** The hiring contact was asked for it. All results
  so far are on three synthetic RFPs written for this exercise:
  - `inputs/rfp_synthetic_main.md`: insurer, GenAI claims triage
  - `evals/rfps/rfp_water_fieldops.md`: water utility field assistant, held out
  - `evals/rfps/rfp_adversarial_council.md`: council RFQ with a prompt injection, held out

  Ingestion accepts md, pdf and docx, so the real brief can be dropped into `inputs/` with no code change. Its gold set would need labelling [eval].
- **"Solution summary" means requirements, approach, risks and open questions,** each traceable to the RFP. Pricing and staffing estimates are out of scope.
- **RFPs are in English,** with numbered sections or headings. Scanned PDFs (no text layer) are not supported; OCR would be an ingest step [ingest].
- **An RFP is up to roughly 30 pages.** Longer documents work (extraction is batched) but take proportionally longer.

## About the user

- **The user is a bid or solution team member** who checks the output, not someone who sends it to a client unread. So the app:
  - shows a verbatim quote for every requirement
  - flags what it is unsure about as open questions
  - never silently drops suspicious text (the injection guard reports it)
- **"Must / should / could" follows the RFP's own wording, not the analyst's view of importance.** Code enforces these words: shall/must/required → must, should/expects/prefers → should, would be welcome/nice to have/optional → could. "May" is left to the model. The prompt suggests "could", but code doesn't force it, because "may … only" is often a limit ("may hold working copies only for as long as needed") rather than an option. One exception: the council RFQ's R2 ("shall … no more than 80 words") was set to `should` in the gold set by human review.

## About the environment

- **Confidentiality matters more than speed.** Client RFPs shouldn't leave the machine, so the pipeline runs locally on Ollama. A hosted model is a config switch (`RFP_PROVIDER=openai_compat`), not the default.
- **Hardware is a 16 GB Apple Silicon laptop.** A full run takes ~11–14 minutes on an M2 Pro. On 8 GB it took ~73 minutes (swap-bound).
- **No paid services are required.** The Claude API is optional: for a stronger judge, or the cost comparison. Costs for hosted models are shown as estimates computed from token counts.
- **Hosted-cost estimates use Nov 2026 list prices** (Haiku 5.5 $0.10/$0.50, Sonnet 5.5 $2/$10 and Opus 5.5 $4/$20 per million tokens). Tokens are counted by the local model's tokenizer, so hosted figures are approximate.

## About the evaluation

- **Gold sets were drafted by Claude and reviewed by Tanya** (all three, 2026-11-21 and 2026-11-22). Every label is hers to defend. The changes she made are listed in `notes/phase2_eval.md` ("Gold review status").
- **"Core" gold items are clear obligations; "optional" items are debatable** (objectives, scope bullets, bid-format asks). Only core items count toward recall.
- **The local LLM judge is indicative only.** It agreed with a human 50% of the time on description faithfulness (n=12) and missed both constraint violations a human found.
