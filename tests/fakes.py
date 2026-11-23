"""Offline test doubles: a scripted LLM client with deterministic embeddings."""

from __future__ import annotations

import hashlib
import re
import time
from typing import Any, Callable

import numpy as np
from pydantic import BaseModel

from rfp_agent.tracing import record_call

Script = BaseModel | dict | Callable[[list[dict[str, str]]], Any]


class FakeLLMClient:
    """Returns scripted responses per node, in order (the last one repeats).

    A script item can be a Pydantic object, a dict (validated against the requested
    schema) or a callable ``(messages) -> object`` for responses that depend on the
    prompt (e.g. covering whatever requirement ids the prompt lists).
    """

    model = "fake-llm"

    def __init__(self, scripts: dict[str, list[Script]]):
        self.scripts = {k: list(v) for k, v in scripts.items()}
        self.calls: list[dict[str, Any]] = []

    def chat_structured(self, messages, schema, node_name, temperature=0.0, prompt_version="-"):
        queue = self.scripts.get(node_name)
        if not queue:
            raise AssertionError(f"no scripted response for node {node_name!r}")
        item = queue.pop(0) if len(queue) > 1 else queue[0]
        if callable(item) and not isinstance(item, BaseModel):
            item = item(messages)
        result = item if isinstance(item, schema) else schema.model_validate(
            item.model_dump() if isinstance(item, BaseModel) else item)
        self.calls.append({"node": node_name, "schema": schema.__name__, "messages": messages})
        record_call(node=node_name, kind="chat", model=self.model, prompt_version=prompt_version,
                    prompt_tokens=sum(len(m["content"]) // 4 for m in messages),
                    completion_tokens=len(result.model_dump_json()) // 4, latency_ms=1.0,
                    retries=0, success=True)
        return result

    def embed(self, texts, node_name="embed"):
        start = time.perf_counter()
        out = [hash_embed(t) for t in texts]
        record_call(node=node_name, kind="embed", model="fake-embed", prompt_version="-",
                    prompt_tokens=0, completion_tokens=0,
                    latency_ms=(time.perf_counter() - start) * 1000, retries=0, success=True)
        return out


def hash_embed(text: str, dim: int = 256) -> list[float]:
    """Bag-of-words hashing embedding: same words -> same vector. Prefixes ignored."""
    text = re.sub(r"^(search_document|search_query|clustering): ", "", text)
    v = np.zeros(dim, dtype=np.float32)
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        v[int(hashlib.md5(w.encode()).hexdigest(), 16) % dim] += 1.0
    if not v.any():
        v[0] = 1.0
    return v.tolist()


def ids_in_prompt(messages, label: str = "Must-priority ids that need coverage:") -> list[str]:
    for m in messages:
        for line in m["content"].splitlines():
            if line.startswith(label):
                return [x.strip() for x in line[len(label):].split(",") if x.strip()]
    return []
