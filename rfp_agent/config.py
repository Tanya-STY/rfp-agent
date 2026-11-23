"""Runtime configuration.

Every knob lives here and can be overridden with an environment variable prefixed
``RFP_`` (e.g. ``RFP_CHAT_MODEL=llama3.1:8b``) or a ``.env`` file in the repo root.
Prompt versions are NOT configured here: each prompt file carries its own ``version``
in front-matter (single source of truth) and that version is written to every trace.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RFP_", env_file=".env", extra="ignore")

    # --- LLM provider -----------------------------------------------------------------
    provider: Literal["ollama", "openai_compat"] = "ollama"
    base_url: str = "http://localhost:11434"
    api_key: str = ""  # only used by the OpenAI-compatible client
    chat_model: str = "qwen2.5:7b"
    embed_model: str = "nomic-embed-text"
    num_ctx: int = 8192  # context window requested from Ollama
    request_timeout_s: float = 900.0
    keep_alive: str = "30m"  # keep the model resident between sequential calls
    max_output_tokens: int = 2048  # num_predict cap: stops runaway generations
    structured_retries: int = 2  # re-asks after invalid JSON / schema violations
    trace_payloads: bool = True  # store raw model output in trace.jsonl (local debugging)

    # --- Per-agent sampling temperatures --------------------------------------------------
    temperature_extract: float = 0.0
    temperature_design: float = 0.2
    temperature_risk: float = 0.0  # 0.2 until phase 2: risks varied run to run
    temperature_critic: float = 0.0

    # --- Workflow ------------------------------------------------------------------------
    max_revisions: int = 2  # critic -> node feedback loops before we give up and assemble
    max_tool_calls: int = 3  # search_rfp budget for the solution architect (whole node)
    retrieval_top_k: int = 4
    max_ids_per_approach_item: int = 12  # larger items are "catch-alls" (failure log F6)
    max_requirements_per_design_call: int = 12  # per workstream group call (25 dropped most must ids in run 6, F18)
    extract_batch_chars: int = 2400  # 3500 tried in run 8: truncation + split, extraction 30% slower (F19)
    max_section_chars: int = 2400  # longer sections are split into overlapping chunks
    chunk_overlap_chars: int = 300
    retrieval_chunk_chars: int = 900
    dedupe_similarity: float = 0.915  # cosine threshold for merging duplicates (tuned on run 2, see notes)
    quote_match_threshold: float = 90.0  # rapidfuzz partial_ratio needed to count as grounded
    risk_context_chars: int = 6000  # cap on retrieved risk context (was 4000 on the 8 GB machine; F17)
    # Sections about the bidding process (how proposals are scored / submitted) are not
    # requirements on the solution: excluded from extraction, still searchable (log F15).
    # Set to "" to extract everything.
    # Context sections: only requirements whose quote states an obligation are kept (F19).
    context_section_titles: str = (r"current (environment|state|situation)|background"
                                   r"|introduction|as-is|existing (systems|environment)")
    extract_skip_titles: str = (r"submission instructions|instructions (to|for) (bidders|tenderers)"
                                r"|evaluation criteria|evaluation methodology|proposal format")

    # --- Eval LLM judge (python -m rfp_agent eval --judge) -----------------------------
    # A different model family from the pipeline, so the judge does not share its blind spots.
    judge_model: str = "llama3.1:8b"
    judge_sample_requirements: int = 20  # requirements judged per run (seeded sample)
    temperature_judge: float = 0.0

    # --- Cost accounting (USD per 1M tokens). Local Ollama is free; set for hosted APIs.
    price_input_per_1m: float = 0.0
    price_output_per_1m: float = 0.0

    # --- Observability: OpenTelemetry export (e.g. Phoenix: http://localhost:6006/v1/traces)
    otel_endpoint: str = ""  # empty = off; the JSONL trace is always written

    # --- Paths ---------------------------------------------------------------------------
    prompts_dir: Path = REPO_ROOT / "prompts"
    runs_dir: Path = REPO_ROOT / "runs"
    cache_dir: Path = REPO_ROOT / ".cache"


def get_settings(**overrides) -> Settings:
    """Build settings from env, then apply explicit overrides (e.g. from the CLI)."""
    clean = {k: v for k, v in overrides.items() if v is not None}
    return Settings(**clean)
