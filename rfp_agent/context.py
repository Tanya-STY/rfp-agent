"""Run-scoped dependencies shared by all nodes.

Kept out of the LangGraph state on purpose: the state holds only plain, serialisable
pipeline data (requirements, risks, feedback...), while heavyweight or non-serialisable
things (HTTP client, vector index, tracer) live here and are captured by node closures.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from .config import Settings
from .ingest import Document
from .llm import LLMClient
from .prompts import Prompt, load_prompt
from .retrieval import VectorIndex
from .tracing import Tracer

log = logging.getLogger("rfp_agent")


@dataclass
class RunContext:
    settings: Settings
    client: LLMClient
    tracer: Tracer
    doc: Document | None = None
    index: VectorIndex | None = None
    prompt_versions: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def warn(self, message: str) -> None:
        """Non-fatal problem: logged, traced and surfaced in the final report."""
        log.warning("  %s", message)
        self.warnings.append(message)
        self.tracer.event("warning", message=message)

    def prompt(self, name: str) -> Prompt:
        p = load_prompt(name, str(self.settings.prompts_dir))
        self.prompt_versions[p.name] = p.version
        return p

    def search(self, query: str, k: int | None = None, node: str = "retrieval"):
        assert self.index is not None, "index not built - ingest must run first"
        return self.index.search(query, self.client, k or self.settings.retrieval_top_k,
                                 node_name=node)
