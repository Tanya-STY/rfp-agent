# Phase 1 - failure log (live runs against qwen2.5:7b on an 8 GB M2)

Each entry: what happened, evidence, fix, result. Feeds DECISIONS.md in Phase 4.

## F1. Generation is swap-bound: 1.4-5 tokens/s

- **What happened:** First timing probe of `qwen2.5:7b` (Q4, 4.7 GB) on the 8 GB M2.
  Prompt eval ~40-60 tok/s, generation only **1.4-3.5 tok/s**; a single extraction batch
  (1 section, 1,019 prompt tokens, 1,121 completion tokens) took **234 s**.
- **Evidence:** `ollama ps` showed the model split `15%/85% CPU/GPU` at num_ctx 8192 and
  still `6%/94%` at num_ctx 4096; `sysctl vm.swapusage` showed 4.4 GB of 5 GB swap in use
  with Chrome/Discord/Claude resident. The model does not fit fully in the GPU working
  set, so every token pays for CPU offload + paging.
- **Fix / mitigations in code:** (1) the model is never asked for anything code can
  compute - ids, section verification, dedupe, numbering, coverage checks are all
  deterministic; (2) `num_predict` capped (`max_output_tokens=1536`) so a runaway
  generation cannot eat 10 minutes; (3) sections packed into ~3,500-char batches
  (fewer calls, less repeated system prompt); (4) description capped at 20 words in the
  prompt; (5) revisions re-extract only the passages the critic points at, not the doc;
  (6) `keep_alive=30m` so the model is not reloaded between sequential calls.
- **Not fixable in code:** throughput is dominated by host memory pressure. Closing
  other apps, or using a smaller model (`RFP_CHAT_MODEL=qwen2.5:3b`), is the lever.
  num_ctx 4096 was not reliably faster (2.2 tok/s vs 3.5 at 8192 in back-to-back probes
  - noise from swap dominates), so num_ctx stays 8192 as briefed; the architect's
  tool-loop context needs ~6k tokens anyway.

## F2. Every requirement marked "must", including "should" requirements

- **What happened:** Smoke test on section 6 (NFRs): all 9 extracted requirements came
  back `priority: must`, although NFR-1 and NFR-5 say "should".
- **Evidence:** `must non_functional S08 100 Scalability for other lines of business |
  **NFR-5 Scalability.** The architecture should allow ...`
- **Fix:** prompt v1.1.0 ties priority to the modal verb *in the quote*, with a mapping
  table and an explicit counter-example ("should allow X is should, even if X sounds
  important").
- **Result:** partly - the model still marks some "should" items must; fixed in code by priority calibration (F4).
- Grounding on this batch was perfect: 9/9 quotes matched at 100 (the short-sentence
  rule works); the model copies the bold label too (`**NFR-1 Performance.** ...`), which
  is fine - it is verbatim, and helps the numbered-coverage check.

## F3. Dense batches overflow `num_predict` -> truncated JSON -> expensive retry

- **What happened:** Live run 1 (`runs/live1`). Batch 2 (scope in/out + current
  environment, 3,002 prompt tokens) produced more requirements than fit in the 1,536-token
  output cap. The JSON was cut off mid-object; the generic retry ("your reply was invalid,
  be concise") re-generated the whole answer. The batch cost **478 s and 2,526 completion
  tokens** for one usable answer. Batch 3 (the FR section alone) used 1,392 tokens - 90%
  of the cap - so it was one requirement away from the same failure.
- **Evidence:** `trace.jsonl`: `extract_requirements 3002 2526 478s retries=1`.
- **Fix:** (1) truncation (`done_reason == "length"`) is now its own exception,
  `OutputTruncatedError`, raised immediately with no same-prompt retry, since re-asking
  the identical question mostly reproduces the identical long answer; (2) the extractor
  catches it and **splits the batch in half** (by section, or by paragraph for a single
  section) and recurses up to depth 2; (3) batches and max section size reduced from
  3,500 to 2,400 chars, and `num_predict` raised to 2,048, so the expected output per call
  sits well under the cap. Unit test: `test_truncated_extraction_batch_is_split_and_retried`.
- **Also added:** `trace_payloads` (default on) stores raw model output in the trace, as
  run 1 gave no way to inspect what the truncated batch had produced.
- **Result:** run 2 - no truncation; largest batch used 1,883 of 2,048 tokens.

## F4. Over-extraction: context facts become "must" requirements (104 raw / 92 after dedupe)

- **What happened:** Live run 2 (`runs/live2`), extraction prompt v1.1.0. The "Current
  Environment" section yielded 13 "requirements" such as *Use ClaimsNet*, *Two data
  centres*, *Limited Azure footprint*, *No REST API*, all `must`. Some single sentences
  were split into 2-3 requirements with the same quote. Submission/evaluation sections
  added proposal-formatting "requirements". Total 104 drafts -> 92 after dedupe, vs. ~45
  real obligations in the document.
- **Evidence:** `trace.jsonl` raw outputs (now stored via `trace_payloads`); e.g.
  `must integration S06 100 Two data centres | The Company operates two data centres...`.
  Also: one open question was copied verbatim from the prompt's worked example
  ("What is the target report generation time?").
- **Cost of the failure:** over-extraction is the main driver of run time (each
  requirement is ~110 output tokens at ~4.5 tok/s, so ~25 s each) and it floods the
  architect with ids (see F6).
- **Fix:** prompt v1.2.0 - explicit context-vs-requirement contrast pair, "one
  requirement per obligation", a non-requirement sentence in the worked example, a
  "never copy the example's questions" line, and compact JSON output. Plus a
  deterministic **priority calibration** from modal verbs in the verified quote
  (`shall/must` -> must, `should/expected/prefers` -> should, `would be welcome/nice to
  have/optional` -> could; ambiguous or modal-free quotes keep the model's call). The
  modal mapping deliberately ignores "may" ("may hold working copies only..." is a
  restriction, not an option). Grounding itself was excellent: 104/104 quotes matched at
  100 - the short-sentence rule plus snapping works.
- **Result:** run 3 - context facts fixed, list-splitting got worse (F11).

## F5. Dedupe threshold: nomic-embed-text similarities are compressed into 0.8-0.95

- **What happened:** with `dedupe_similarity=0.93`, run 2 merged only 12 of the obvious
  duplicates; scope bullets vs. the numbered FRs they summarise ("Ingest claim
  documents" vs "Multi-channel ingestion", 0.921; "Use IBM MQ" vs "Policy coverage
  lookups using existing IBM MQ", 0.917) survived.
- **Evidence:** pairwise cosine over the 104 drafts (`clustering:` prefix): true
  duplicates 0.917-0.953, clearly distinct pairs as high as 0.898 ("Triage claims" vs
  "Claim triage and routing availability"), unrelated pairs ~0.80-0.85.
- **Fix:** threshold lowered to **0.915**, inside the gap between 0.898 and 0.917. The
  band is narrow, so this is a tuned constant, not a law - flagged for the Phase 2
  eval harness (precision/recall of dedupe on a labelled pair set).
- **Also found:** identical-quote merging collapsed two different obligations the model
  had split out of one sentence ("Near real-time read access" + "No write access").
  Prompt v1.2.0's "one requirement per obligation" rule addresses the root cause.

## F6. Architect games the must-coverage check with a 60-id catch-all item

- **What happened:** run 2, design prompt v1.0.0. With 70+ must ids to cover, the
  model's first approach item listed **60 requirement ids** with a generic summary
  ("Develop a solution that integrates with ClaimsNet, IBM MQ, DMS..."), so the
  deterministic must-coverage check passed while the approach was useless.
- **Evidence:** `design_approach` output in `runs/live2/trace.jsonl`.
- **Fix:** design prompt v1.1.0 (example workstream names, "at most N ids per item",
  "catch-all items are rejected") and a new deterministic critic check,
  `approach_granularity` (`max_ids_per_approach_item=12`), routed to the architect as a
  blocking issue. Reducing over-extraction (F4) also shrinks the coverage burden.
- **Tool loop observation:** the bounded search loop behaved well - one search
  ("legacy system details", top hits from the Current Environment section), then final.
  Structured `action` output had zero parse failures.

## F7. Risk analyst repetition loop: the same risk emitted 5 times

- **What happened:** run 2, risk prompt v1.0.0, temperature 0.2. Risks 6-10 were
  identical copies of "Ambiguity in 'explain routing decisions'".
- **Evidence:** `analyze_risks` output in `runs/live2/trace.jsonl`.
- **Fix:** deterministic `drop_repeats` (normalised-title equality) before ids are
  assigned, with a warning surfaced in the report. The *content* of the first five risks
  was good: it found the planted tension (fixed 30 June pilot vs 16-20 week hardware
  procurement), the ambiguity, and the 30-day deletion vs SIU retention tension.
- **Also:** risk-context retrieval made 8 separate embedding calls (one per query);
  replaced with `VectorIndex.search_many` (one batched call).

## F8. Dedupe kept the vague duplicate, so the critic flagged a numbered requirement as missing

- **What happened:** run 2's critic raised `numbered_coverage: RFP requirement FR-7
  (section S07.1) was not extracted` - although FR-7 *had* been extracted. Dedupe merged
  it with the one-line scope bullet "Fraud-indicator flagging for referral to SIU." and
  kept the bullet (tie-break was priority, then confidence).
- **Evidence:** `dedupe` event `merged: [["Fraud indicator flagging", "Identify fraud
  indicators"], ...]` followed by the `critic_report` event.
- **Fix:** dedupe now prefers (grounded, then **longest quote**, then confidence), so the
  specific, labelled paragraph survives. The critic did its job here: it caught a real
  loss of traceability and routed a targeted re-read of just that passage.

## F9. Architect output truncated on revision -> empty approach -> extra revision

- **What happened:** run 2, revision 1. After re-extraction the architect (prompt
  v1.0.0) tried to list ~94 requirement ids across items and hit `num_predict=2048`
  mid-JSON. The new `OutputTruncatedError` propagated, the architect returned no
  approach, the critic raised `must_coverage: No approach items produced` (blocking),
  and the second (last) revision was spent re-running the architect. Cost: ~7 min.
- **Evidence:** trace: `design_approach ... completion_tokens 2048 ... error "truncated at
  num_predict"`; warnings `architect step failed` / `architect did not return a final
  approach`; critic history pass 1.
- **Fix:** on truncation the architect now gets one tighter re-ask ("at most 7 items, <=12
  ids each, one-sentence summary, <=3 components") inside its bounded loop, instead of
  giving up. Root causes are also addressed by F4 (fewer requirements) and F6 (id cap
  per item).
- **Result of run 2 overall:** completed and critic passed after 2 revisions, but
  wall time **72.8 min** (extraction alone 38 min), 94 requirements (inflated), 14
  approach items, 6 risks. Totals: 46 LLM calls, 53.5k prompt / 20.2k completion
  tokens. The revision loop worked mechanically (targeted re-read of 1 passage took
  45 s instead of a 38-min re-extraction).

## F10. LLM critic is noisy; only deterministic checks were worth blocking on

- **What happened:** across 3 critic passes in run 2 the LLM review raised 15 issues,
  none `high`. Several were wrong ("FR-18 [no auto-decline] violates INT-10 [no writes to
  the policy system]") or vague ("FR-03 and FR-04 are closely related"). One was
  genuinely useful (an unlisted tension between minimising PII exposure and retaining
  working copies).
- **Decision (validated):** only `high` severity blocks, and every check that can be done
  in code is done in code. The LLM's medium/low issues are recorded in the report's
  critic history for a human, not used to drive loops. All three blocking issues in run
  2 came from deterministic checks and all three were real.

## Live run 3 (`runs/live3`, extraction v1.2.0, design v1.1.0) - stopped after design

Run 3 was stopped deliberately once the architect output showed F12 (no point spending
another 25 min on a known-bad design pass). What it showed:

- **F4 fix worked for context facts:** "Current Environment" produced 0 requirements
  (vs 13 in run 2) and 6 open questions instead; that batch took 48 s instead of 225 s.
  Compact JSON output was honoured (`{"requirements": [], ...}` with no indentation).
- **Priority calibration** changed 9/100 priorities, e.g. "Single doc classification under
  30 seconds" must -> should ("should complete"), "Team based in Malaysia" should -> must
  ("must be based in Malaysia").
- Still 100 drafts -> 84 after dedupe, 35 min extraction - see F11.

## F11. "One requirement per obligation" backfired: lists split per item, quotes shared

- **What happened:** v1.2.0's rule was read as "split every list". One scope bullet
  ("Triage: complexity scoring, line-of-business routing and adjuster queue assignment")
  became 3 requirements sharing one quote; "Bidders should explain how they will evaluate
  model quality..." became 5. The identical-quote dedupe rule then merged them back -
  but it also merged **"Support Bahasa Malaysia" (should) with "Support Chinese documents"
  (could)**, which the model had extracted from one two-sentence quote. That silently
  destroyed the buried nice-to-have and its distinct priority.
- **Evidence:** `dedupe` event in `runs/live3/trace.jsonl`: `["Support Bahasa Malaysia",
  "Support Chinese documents"]`; their cosine similarity was only 0.793.
- **Fix:** (1) identical quote alone no longer merges; it needs quote equality **and**
  cosine >= 0.85 (the eval-capability splits at 0.75-0.84 and the language pair at 0.79
  stay separate; over-granularity is a lesser evil than losing a distinct requirement);
  (2) prompt v1.3.0: "if one sentence lists several items, extract ONE requirement for
  that sentence; two requirements never share a quote", and "do not join text from
  different lines or list items". Unit test:
  `test_dedupe_merges_duplicates_but_keeps_distinct_obligations_sharing_a_quote`.

## F12. Stitched quotes from numbered lists (caught by grounding)

- **What happened:** for "Proposals should contain: 1. ... 2. A requirements compliance
  matrix ...", the model built quotes like `Proposals should contain: 2. A requirements
  compliance matrix responding to every...` - plausible but not verbatim.
- **Evidence:** quote_in_source scores 72-88 for 6 of the 10 S15 requirements (below the
  90 threshold); the deterministic critic would have routed them back for re-extraction.
- **Fix:** v1.3.0 forbids joining list items. This is exactly the failure the grounding
  check exists for: none of those quotes would have reached the summary unflagged.

## F13. Architect still made a catch-all with 84 requirements - design now per workstream

- **What happened:** with design prompt v1.1.0 ("at most 12 ids per item") the model
  still returned only 2 items, one with 47 ids (several listed twice) and no
  components. Prompt rules alone cannot make a 7B model juggle 84 ids in one answer.
- **Fix (structural, not prompt):** the architect now runs one bounded tool loop per
  **workstream group** (functional / platform qualities / security+integration /
  delivery+commercial; groups over 25 requirements are chunked), sharing a single
  search budget of 3 across the node. Each call sees <= 25 ids and returns 1-4 items.
  Design prompt v2.0.0. The deterministic `approach_granularity` check stays as the
  safety net.
- **Result:** offline tests only (live run 4 was stopped before reaching design).

## Live run 4 (`runs/live4`) - stopped after 2 batches (machine change)

Started with every fix above (extraction v1.3.0, design v2.0.0 per-workstream), then
stopped after 2 extraction batches because the project is moving to a more powerful Mac.
One finding from those 2 batches: **v1.3.0 did not stop list-splitting.** The scope
bullet "Document classification, data extraction and claim summarisation" still became
3 requirements sharing one quote, and the triage bullet 3 more. Dedupe (quote equal +
cosine >= 0.85) will merge the first group (0.78-0.86 in run 3: partially) but not the
triage split (0.65-0.73). Accepting over-granularity for now; see next steps.

## Summary of live runs on the 8 GB M2

| Run | Prompts (extract / design) | Outcome | Wall time | Chat calls | Prompt / completion tokens | Reqs (raw -> dedupe) | Approach items | Risks | Critic |
|---|---|---|---|---|---|---|---|---|---|
| live1 | 1.0.0 / 1.0.0 | stopped after 3 batches (F3) | ~16 min | 3 | 5.8k / 4.5k | - | - | - | - |
| live2 | 1.1.0 / 1.0.0 | **complete** (`runs/sample/phase1-live2/`) | 72.8 min (extraction 38 min) | 24 | 43.8k / 20.2k | 104 -> 92 (94 after revision) | 14 | 6 (10 before repeats) | FAIL, FAIL, PASS - 2 revisions |
| live3 | 1.2.0 / 1.1.0 | stopped after design (F13) | 38 min to design | 13 | 18.9k / 11.1k | 100 -> 84 | 2 (one with 47 ids) | - | - |
| live4 | 1.3.0 / 2.0.0 | stopped after 2 batches (machine change) | 6 min | 2 | 2.8k / 1.6k | - | - | - | - |

Embedding calls are excluded above (cheap: <1 s each after the first load). All costs
$0 (local). Grounding was the strongest part throughout: every quote from extraction in
runs 2-4 scored 100 except the stitched list quotes in run 3 (F12), which the check
caught. Generation speed was 4-5 tok/s throughout, so time is ~proportional to output
tokens; extraction dominates.

**What still looks wrong (not validated live after the fixes):**
- Requirement count is still inflated (84-94 vs ~45-50 genuine obligations), driven by
  list-splitting (F11, run 4) and bidding-process items from Evaluation Criteria /
  Submission Instructions.
- Run 3's approach (2 items, 47-id catch-all) is the reason the architect became
  per-workstream (F13); that redesign has only been tested offline.
- Risk related-ids are weak: run 2's headline tension (pilot date vs procurement) cited
  TL/INT ids but not the data-residency requirement (SEC) that causes it.
- LLM critic feedback is mostly noise (F10); it never blocked anything.
- Total runtime: 73 min on this machine. Too slow for an iteration loop; acceptable only
  as a one-off.

## Next steps (validate live on the new machine)

1. **Full end-to-end run with current code** (extract v1.3.0, design v2.0.0):
   `python -m rfp_agent run --input inputs/rfp_synthetic_main.md`. Check: wall time,
   requirement count, that the architect returns 1-4 items per group with no
   `approach_granularity` issues, and that no risks are repeated.
2. **Check that F4/F11 fixes hold together:** count requirements sharing a quote
   (`summary.json`); if list-splitting persists, consider merging same-quote
   requirements from the same *list bullet* in code, or a "list items -> one
   requirement" example in the prompt.
3. **Check the Chinese-language nice-to-have survives** as a separate `could`
   requirement (the planted buried nice-to-have), and the Bahasa one as `should`.
4. **Check the planted tension and ambiguity are found:** a `requirement_conflict` risk
   linking the 30 June pilot (TL) with SEC-1 residency / hardware lead time, and an
   `ambiguity` risk for "real time" in NFR-1. Consider adding "cite the requirement ids
   on BOTH sides of a tension" to the risk prompt if SEC is still missing.
5. **Watch the revision loop on real data:** whether grounding failures (F12) get
   repaired by the targeted re-read, and whether anything is dropped at assembly.
6. **Re-tune `dedupe_similarity` (0.915)** if the embedding model changes; the gap
   between true duplicates and distinct pairs was narrow (0.898 vs 0.917).
7. **Timing baseline:** record per-node latency and tok/s from `trace.jsonl` on the new
   machine; if generation is >20 tok/s, consider raising `extract_batch_chars` back
   toward 3,500 (fewer calls) while keeping truncation splitting as the safety net.
8. Possibly exclude bidding-process sections (evaluation criteria, submission
   instructions) from extraction, or categorise them separately - a scoping decision.

---

# Phase 1b - live runs on the 16 GB M2 Pro (2026-11-21)

Machine: M2 Pro, 16 GB, macOS 13.6. The Ollama app and current CLI (v0.40) need macOS 14
(the CLI starts, but its Metal runner aborts on model load, `GGML_ASSERT(buf_dst)`), so
the runs use the official **Ollama v0.11.10** CLI build (min macOS 13.0). The model is
100% on GPU; `qwen2.5:7b` generates at ~34 tok/s in isolation, ~15-26 tok/s effective
per call including prompt evaluation (step 7 baseline below).

## Live run 5 (`runs/live5`) - current code from Phase 1, unchanged

Complete in **19.1 min** (vs 72.8 min for run 2), 0 errors / 0 retries, but the critic
failed all three passes and both revisions changed nothing:

| node | calls | prompt tok | output tok | time | effective out tok/s |
|---|---|---|---|---|---|
| extract_requirements | 13 | 17.7k | 12.2k | 463 s | 26.3 |
| design_approach | 30 | 34.8k | 9.4k | 403 s | 23.3 |
| analyze_risks | 3 | 12.4k | 3.1k | 179 s | 17.2 |
| critic | 3 | 10.7k | 1.3k | 91 s | 14.8 |

Checks against the handoff's next steps:
- **Chinese nice-to-have** survived as its own `could` (FR-27), Bahasa as `should` (FR-26). OK.
- **Planted tension** found (pilot date vs hardware procurement, `requirement_conflict`)
  and the **"real time" ambiguity** found - but the tension again cited only TL/COM ids,
  not the SEC data-residency requirement; the deletion-vs-SIU tension was missed.
- **Requirement count** 101 (94 after dropping ungrounded); 19 came from Evaluation
  Criteria / Submission Instructions. 5 quote-sharing pairs remain.
- **Revision loop** (step 5): did not repair anything - see F14, F16.
- **Dedupe threshold** (step 6): embedding model unchanged; 0.915 left as is.
- **Batch size** (step 7): generation is now >20 tok/s, but `extract_batch_chars` was
  left at 2,400 to change one thing at a time; truncation splitting stays the safety net.

## F14. Stitched quotes survive every revision; the re-read never replaces them

- **What happened:** the same 7 grounding failures in all 3 critic passes. 6 were list
  items glued to their lead-in ("Proposals should contain: 2. A requirements compliance
  matrix ..."), 1 a label glued to a later sentence ("**NFR-3 Availability.** Planned
  maintenance must be ..."). The targeted re-read added new drafts but the graph kept
  the old ungrounded requirements alongside them, and the model re-stitched the same way.
- **Fix:** (1) `extractor.stitch_candidates`: when a quote fails, the tail after a leading
  label / last list marker / last colon is tried as a quote on its own (>= 25 chars, must
  snap to an exact span). All 7 run-5 quotes now ground at 100; a hallucinated list item
  still fails (test). (2) On revision, requirements flagged by `grounding` are replaced
  by the re-read instead of merged with it.

## F15. Bidding-process sections produce "requirements" (scoping decision, step 8)

- **What happened:** Evaluation Criteria and Submission Instructions yielded 19 of 101
  requirements in run 5 ("Electronic submission", "Proposal length limit", "Solution fit
  evaluation") and 6 of the 7 grounding failures. The prompt already says proposal
  formatting is not a requirement; the 7B model ignores it.
- **Decision:** they are not requirements on the solution. Sections whose title matches
  `extract_skip_titles` (submission instructions, evaluation criteria, instructions to
  bidders, proposal format) are not extracted, and the critic's labelled-requirement
  check ignores them. They stay in the retrieval index, so the architect and risk
  analyst can still read them. `RFP_EXTRACT_SKIP_TITLES=""` restores the old behaviour.

## F16. Architect: whole-node feedback creates catch-alls; unknown ids never get fixed

- **What happened:** run 5 revision 1 sent the critic's must-coverage feedback (~30 ids
  from all groups) to every workstream group. Each group put them into one item:
  54 items, including a 33-id and a 22-id catch-all, and ids that do not exist
  (INT-12..14). Unknown ids (also in risks) survived both revisions.
- **Fix:** (1) `feedback_for_group` passes each group only feedback about its own ids,
  with id lists cut to the group. (2) `check_group_answer` validates every group's final
  answer in code (all must ids covered, <= 12 ids per item, no unknown ids) and gives the
  model ONE correction turn inside the group's loop. (3) ids still unknown after that are
  dropped with a warning (architect and risk analyst) instead of spending a revision.

## F17. Risk context: score-only ranking crowds out topics

- **What happened:** with a 4,000-char cap and pure score ranking, risk context came from
  S09-S12 only; the performance passage and the 30-day deletion rule (S10.2) never
  reached the analyst. (The data-residency passage *was* present - the model simply did
  not cite SEC ids.)
- **Fix:** the top hit of every risk query is taken first, then the rest by score; cap
  raised to 6,000 chars (affordable at current speed). Risk prompt v1.1.0 asks for the
  ids on BOTH sides of a tension, including the constraint that causes it.

## Live run 6 (`runs/live6`) - F14-F17 applied

17.0 min. **0 deterministic issues** on passes 1 and 2 (no grounding failures, no catch-
alls, no unknown ids; 0 requirements dropped). 91 requirements (none from S14/S15).
Risks improved: residency now cited (R-03 SEC-01), the deletion-vs-SIU tension found
(R-05), the pilot/procurement tension and "real time" ambiguity found again. Two new
problems drove both revisions - F18.

## F18. LLM critic "high" false positives block; 25-requirement groups drop must ids

- **What happened:** (1) the LLM reviewer rated two issues "high": the approach "uses
  Azure" and "uses a REST API". Both false - the approach says "Ensure no REST API is
  used" and "avoiding the use of Microsoft Azure". These blocked passes 1 and 2 and sent
  the architect back twice. (2) The first functional group had 25 requirements; the
  model left 19 must ids out, the correction turn recovered only some, and the final
  pass failed must_coverage with 9 missing.
- **Fix:** (1) the LLM review is advisory: its issues are capped at medium (prefixed
  "[LLM reviewer rated high]") and never block - the decision F10 argued for, now
  enforced in code. (2) `max_requirements_per_design_call` 25 -> 12.

## Live run 7 (`runs/live7`) - F14-F18 applied: **critic PASS**

**14.5 min**, critic failed pass 0 on one deterministic must-coverage gap, the architect
fixed it in revision 1, pass 1 **PASSED** (0 deterministic issues, 0 blocking). 0 errors,
0 retries, 0 requirements dropped, 0 warnings. Extraction is deterministic (temperature 0):
identical 91 requirements and token counts as run 6.

- 39 approach items, max 12 ids per item, **every must requirement covered**.
- 10 risks, no repeats: pilot date vs hardware procurement (R-01), deletion vs SIU
  retention (R-03), three ambiguities incl. "near real-time" / "real-time" (R-02, R-05).
- Chinese (`could`) and Bahasa (`should`) kept as separate requirements.
- Architect correction turns fired in 5 of 9 groups and fixed every gap within the group.

## Summary of live runs on the 16 GB M2 Pro

| Run | Changes | Wall time | Chat calls | Prompt / output tokens | Reqs | Approach | Risks | Critic |
|---|---|---|---|---|---|---|---|---|
| live5 | Phase 1 code | 19.1 min | 50 | 89.6k / 26.1k | 101 (94 after dropping 7 ungrounded) | 26 | 5 | FAIL x3 |
| live6 | F14-F17 | 17.0 min | 50 | 74.5k / 24.3k | 91 | 20 | 6 | FAIL x3 (LLM false positives, F18) |
| live7 | + F18 | **14.5 min** | 47 | 57.3k / 21.2k | 91 | 39 | 10 | FAIL, **PASS** |

## Still open after Phase 1b

1. **Context facts extracted again** (F4 regression): "Two data centres in Malaysia",
   "Limited use of Microsoft Azure", "No REST API" come from Current Environment (S06,
   10 requirements). Run 3 had 0 from S06 with the same prompt rule, so this varies with
   batch packing. They also feed bad LLM-critic claims (F18). Options: a deterministic
   "context section" flag, or a second contrast example from S06-style text.
2. **Quote sharing:** 6 groups (one sentence in S13 -> 5 requirements). Accepted as
   over-granularity for now (F11); a same-quote + same-section merge would fix it.
3. **Requirement count** 91 vs ~45-50 genuine obligations - mainly (1) and (2).
4. **Main tension still lacks the SEC id:** R-01 cites TL-03 + COM-12 (procurement), not
   SEC-01 (residency), even with prompt v1.1.0. SEC-01 is cited elsewhere (R-03, R-10).
   Could be enforced in code (a requirement_conflict risk must cite >= 2 categories).
5. `extract_batch_chars` still 2,400; extraction (400 s, 10 calls) is now the largest
   node - raising it to ~3,500 is the next speed lever to try.

## F19. Over-extraction: context facts and one-sentence splits (open items 1-3, 5)

- **What happened:** run 7 kept 10 requirements from Current Environment (S06), of which
  one states an obligation ("All internal applications must use single sign-on"); the
  rest describe the client ("Two data centres in Malaysia", "Use ClaimsNet", "No REST
  API"). Six quotes were shared, one sentence in S13 by 5 requirements. These fed the
  LLM critic's false claims (F18) and inflated the count to 91.
- **Fix (code, not prompt - prompt rules alone failed in F4/F11):**
  (1) `drop_context_facts`: in sections whose title matches `context_section_titles`
  (current environment, background, introduction, as-is, existing systems) a requirement
  is kept only if its quote states an obligation (the modal-verb classes used by
  priority calibration; "not permitted / not allowed / prohibited" now count as must).
  Implied requirements in other sections are untouched.
  (2) dedupe: identical quote + identical priority merges regardless of similarity, and
  the merged titles are kept in the description ("Also covers: ..."). Same quote with
  different priorities still stays separate (the Bahasa `should` / Chinese `could` case).
  Replayed on run 7's output: 91 -> 76, 0 shared quotes.
- **Batch size (open item 5):** `extract_batch_chars` 2,400 -> 3,500 was tried in run 8.
  One batch truncated and had to be split and re-run; extraction took 519 s vs 400 s.
  Reverted to 2,400. Larger output per call is not worth it even at ~25 tok/s.

## Live run 8 (`runs/live8`) - F19 + 3,500-char batches: critic PASS

21.1 min (slower: the batch-size trial above). 78 requirements (56 must / 18 should /
4 could), **0 shared quotes**, 2 kept from S06 (SSO and the no-write-access rule),
Chinese `could` / Bahasa `should` intact, 38 approach items (max 11 ids), every must
covered, 0 dropped. The revision loop now **repairs** things: pass 0 failed on one
ungrounded quote and the targeted re-read fixed it (first live confirmation of F14);
pass 1 failed on one uncovered must id and the architect fixed it; pass 2 PASSED.

## Live run 9 (`runs/live9`) - final config (F14-F19, 2,400-char batches): **PASS first time**

**11.1 min**, critic **PASSED on the first pass - 0 revisions**, 0 deterministic issues,
0 errors, 0 retries, 0 dropped, 0 warnings. 30 chat calls, 39.8k prompt / 16.5k output.

- 76 requirements (58 must / 15 should / 3 could), 0 shared quotes; 8 context facts
  dropped, 2 kept from S06 (no-write-access rule, AD/SSO).
- Chinese `could` (FR-26) and Bahasa `should` (FR-25) kept separate.
- 47 approach items, max 12 ids, every must covered.
- 7 risks: **R-01 pilot go-live vs SEC-01 data residency** (TL-03 + SEC-01 - the SEC id
  is finally cited), R-03 deletion vs SIU, R-02 "real time" ambiguity, R-04 hardware
  procurement.

| Run | Changes | Wall time | Chat calls | Reqs | Shared quotes | Critic |
|---|---|---|---|---|---|---|
| live5 | Phase 1 code | 19.1 min | 50 | 101 -> 94 | 5 | FAIL x3 |
| live7 | F14-F18 | 14.5 min | 47 | 91 | 6 | FAIL, PASS |
| live8 | + F19, 3,500-char batches | 21.1 min | 62 | 78 | 0 | FAIL, FAIL, PASS (loop repaired both) |
| live9 | F19, 2,400-char batches | **11.1 min** | 30 | **76** | **0** | **PASS (0 revisions)** |

## Still open after run 9

1. **Requirement count** 76 vs ~45-50 genuine obligations. Remaining inflation is mostly
   fine-grained splits of numbered requirements across sentences (e.g. one FR paragraph
   -> 2-3 requirements with different quotes). Needs a labelled gold set to judge which
   are real - Phase 2 evaluation harness.
2. **Run-to-run variance:** each run above is a single sample. Extraction is
   deterministic (temperature 0) but design/risk use 0.2; R-01 citing SEC-01 appeared
   in run 9 only. Phase 2 should measure pass rate and risk recall over N runs.
3. **LLM critic** is now advisory only; its feedback is still mostly noise (F10, F18).
   Worth evaluating whether it adds anything, or dropping it to save ~25 s per pass.
4. Dedupe threshold 0.915 unchanged (embedding model unchanged).
