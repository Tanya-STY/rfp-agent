# Cost report

Local runs on Ollama cost **$0** in API fees (electricity and hardware aside).
The hosted columns show what the same token volume would cost on Claude.

_Tokens are counted by the local model's tokenizer; hosted tokenizers differ (Haiku 5.5 counts ~30% more), and thinking tokens are not included._

| Run | LLM calls | Input tok | Output tok | Model time (min) | Claude Haiku 5.5 | Claude Sonnet 5.5 | Claude Opus 5.5 |
|---|---|---|---|---|---|---|---|
| eval-20261122-001407-1 | 47 | 58,017 | 20,596 | 14.1 | $0.016 | $0.322 | $0.644 |
| eval-20261122-000939-1 | 14 | 17,001 | 6,166 | 4.4 | $0.005 | $0.096 | $0.191 |
| eval-20261122-002816-1 | 13 | 12,593 | 3,601 | 2.5 | $0.003 | $0.061 | $0.122 |

**At 50 RFPs a month** (average of the runs above): Claude Haiku 5.5 $0.40, Claude Sonnet 5.5 $7.98, Claude Opus 5.5 $15.96.

## Where the tokens go (first run)

| Node | Calls | Input tok | Output tok | Model time (s) | Share of cost* |
|---|---|---|---|---|---|
| design_approach | 33 | 31,813 | 9,373 | 376 | 49% |
| extract_requirements | 10 | 13,627 | 9,507 | 355 | 38% |
| critic | 2 | 6,614 | 822 | 55 | 7% |
| analyze_risks | 1 | 4,760 | 792 | 53 | 5% |
| assemble | 1 | 1,203 | 102 | 7 | 1% |

*share of the Claude Haiku 5.5 cost; the split is the same for any model whose output/input price ratio is 5x.
