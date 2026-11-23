"""LLM provider abstraction.

``LLMClient`` is the only interface agents depend on. Swap backends with
``RFP_PROVIDER=ollama|openai_compat`` - no agent code changes.

Why raw ``httpx`` instead of the ``ollama`` python package: the package is a thin
wrapper over httpx anyway; calling the REST API directly gives us (a) one HTTP code path
shared with the OpenAI-compatible client, (b) direct access to the raw response fields
we trace (``prompt_eval_count``, ``eval_count``, ``done_reason``) without depending on
SDK object shapes, and (c) one less dependency to pin.

Structured output: Ollama's native ``/api/chat`` accepts ``format=<JSON schema>`` and
constrains decoding to it. Constrained decoding guarantees *syntax* but not semantics
(e.g. ``confidence`` > 1, truncated output when ``num_predict`` is hit), so we still
validate with Pydantic and, on failure, re-ask up to ``structured_retries`` times with
the validation error fed back to the model.
"""

from __future__ import annotations

import json
import time
from typing import Protocol, TypeVar, runtime_checkable

import httpx
from pydantic import BaseModel, ValidationError

from .config import Settings
from .tracing import record_call

T = TypeVar("T", bound=BaseModel)
Message = dict[str, str]


class StructuredOutputError(RuntimeError):
    """Raised when the model never produced valid output within the retry budget."""


class OutputTruncatedError(StructuredOutputError):
    """The model hit ``num_predict`` mid-JSON. Re-asking the same question rarely helps
    (it regenerates the same long answer), so this is raised immediately and callers
    shrink the task instead - e.g. the extractor splits the batch in half."""


@runtime_checkable
class LLMClient(Protocol):
    model: str

    def chat_structured(
        self,
        messages: list[Message],
        schema: type[T],
        node_name: str,
        temperature: float = 0.0,
        prompt_version: str = "-",
    ) -> T: ...

    def embed(self, texts: list[str], node_name: str = "embed") -> list[list[float]]: ...


def _feedback_message(error: str) -> Message:
    return {
        "role": "user",
        "content": (
            "Your previous reply could not be used: "
            f"{error}\nReply again with ONLY a JSON object that matches the schema. "
            "Keep it concise so it is not cut off."
        ),
    }


class OllamaClient:
    """Fully implemented client for Ollama's native REST API."""

    def __init__(self, settings: Settings):
        self.s = settings
        self.model = settings.chat_model
        self.embed_model = settings.embed_model
        self._http = httpx.Client(base_url=settings.base_url, timeout=settings.request_timeout_s)

    # -- chat -----------------------------------------------------------------------------
    def chat_structured(self, messages, schema, node_name, temperature=0.0, prompt_version="-"):
        convo = list(messages)
        prompt_tokens = completion_tokens = 0
        last_error = "unknown"
        start = time.perf_counter()
        for attempt in range(self.s.structured_retries + 1):
            payload = {
                "model": self.model,
                "messages": convo,
                "stream": False,
                "format": schema.model_json_schema(),
                "keep_alive": self.s.keep_alive,
                "options": {
                    "temperature": temperature,
                    "num_ctx": self.s.num_ctx,
                    "num_predict": self.s.max_output_tokens,
                },
            }
            try:
                resp = self._http.post("/api/chat", json=payload)
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                self._record(node_name, prompt_version, prompt_tokens, completion_tokens,
                             start, attempt, False, f"http: {exc}")
                raise
            data = resp.json()
            prompt_tokens += data.get("prompt_eval_count", 0) or 0
            completion_tokens += data.get("eval_count", 0) or 0
            content = data.get("message", {}).get("content", "")
            try:
                result = schema.model_validate_json(content)
                extra = {"output": content} if self.s.trace_payloads else {}
                self._record(node_name, prompt_version, prompt_tokens, completion_tokens,
                             start, attempt, True, None,
                             done_reason=data.get("done_reason"), **extra)
                return result
            except (ValidationError, json.JSONDecodeError, ValueError) as exc:
                if data.get("done_reason") == "length":
                    self._record(node_name, prompt_version, prompt_tokens, completion_tokens,
                                 start, attempt, False, "truncated at num_predict")
                    raise OutputTruncatedError(
                        f"[{node_name}] output cut off at {self.s.max_output_tokens} tokens"
                    ) from exc
                last_error = _short_error(exc)
                convo = convo + [
                    {"role": "assistant", "content": content[:2000]},
                    _feedback_message(last_error),
                ]
        self._record(node_name, prompt_version, prompt_tokens, completion_tokens, start,
                     self.s.structured_retries, False, last_error)
        raise StructuredOutputError(f"[{node_name}] no valid {schema.__name__}: {last_error}")

    # -- embeddings -------------------------------------------------------------------------
    def embed(self, texts, node_name="embed"):
        start = time.perf_counter()
        vectors: list[list[float]] = []
        tokens = 0
        # Small batches keep memory flat on an 8 GB machine.
        for i in range(0, len(texts), 16):
            resp = self._http.post(
                "/api/embed",
                json={"model": self.embed_model, "input": texts[i : i + 16],
                      "keep_alive": self.s.keep_alive},
            )
            resp.raise_for_status()
            data = resp.json()
            vectors.extend(data["embeddings"])
            tokens += data.get("prompt_eval_count", 0) or 0
        record_call(node=node_name, kind="embed", model=self.embed_model, prompt_version="-",
                    prompt_tokens=tokens, completion_tokens=0,
                    latency_ms=(time.perf_counter() - start) * 1000, retries=0, success=True,
                    n_texts=len(texts))
        return vectors

    def _record(self, node, prompt_version, pt, ct, start, retries, ok, err, **extra):
        record_call(node=node, kind="chat", model=self.model, prompt_version=prompt_version,
                    prompt_tokens=pt, completion_tokens=ct,
                    latency_ms=(time.perf_counter() - start) * 1000, retries=retries,
                    success=ok, error=err, price_input_per_1m=self.s.price_input_per_1m,
                    price_output_per_1m=self.s.price_output_per_1m, **extra)


class OpenAICompatClient:
    """Stub for any OpenAI-compatible endpoint (vLLM, LM Studio, llama.cpp server, ...).

    Implements the same retry/trace contract using ``response_format=json_schema``.
    Not exercised in Phase 1 tests or runs - treat as a starting point.
    """

    def __init__(self, settings: Settings):
        self.s = settings
        self.model = settings.chat_model
        headers = {"Authorization": f"Bearer {settings.api_key}"} if settings.api_key else {}
        self._http = httpx.Client(base_url=settings.base_url, timeout=settings.request_timeout_s,
                                  headers=headers)

    def chat_structured(self, messages, schema, node_name, temperature=0.0, prompt_version="-"):
        convo = list(messages)
        pt = ct = 0
        start = time.perf_counter()
        last_error = "unknown"
        for attempt in range(self.s.structured_retries + 1):
            resp = self._http.post("/v1/chat/completions", json={
                "model": self.model, "messages": convo, "temperature": temperature,
                "max_tokens": self.s.max_output_tokens,
                "response_format": {"type": "json_schema", "json_schema": {
                    "name": schema.__name__, "schema": schema.model_json_schema()}},
            })
            resp.raise_for_status()
            data = resp.json()
            usage = data.get("usage", {})
            pt += usage.get("prompt_tokens", 0)
            ct += usage.get("completion_tokens", 0)
            content = data["choices"][0]["message"]["content"] or ""
            try:
                out = schema.model_validate_json(content)
                record_call(node=node_name, kind="chat", model=self.model,
                            prompt_version=prompt_version, prompt_tokens=pt, completion_tokens=ct,
                            latency_ms=(time.perf_counter() - start) * 1000, retries=attempt,
                            success=True, price_input_per_1m=self.s.price_input_per_1m,
                            price_output_per_1m=self.s.price_output_per_1m)
                return out
            except (ValidationError, ValueError) as exc:
                last_error = _short_error(exc)
                convo += [{"role": "assistant", "content": content[:2000]},
                          _feedback_message(last_error)]
        record_call(node=node_name, kind="chat", model=self.model, prompt_version=prompt_version,
                    prompt_tokens=pt, completion_tokens=ct,
                    latency_ms=(time.perf_counter() - start) * 1000,
                    retries=self.s.structured_retries, success=False, error=last_error)
        raise StructuredOutputError(f"[{node_name}] no valid {schema.__name__}: {last_error}")

    def embed(self, texts, node_name="embed"):
        start = time.perf_counter()
        resp = self._http.post("/v1/embeddings", json={"model": self.s.embed_model, "input": texts})
        resp.raise_for_status()
        data = resp.json()
        record_call(node=node_name, kind="embed", model=self.s.embed_model, prompt_version="-",
                    prompt_tokens=data.get("usage", {}).get("prompt_tokens", 0),
                    completion_tokens=0, latency_ms=(time.perf_counter() - start) * 1000,
                    retries=0, success=True)
        return [d["embedding"] for d in data["data"]]


def _short_error(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        errs = exc.errors()[:5]
        return "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in errs)
    return str(exc)[:300]


def make_client(settings: Settings) -> LLMClient:
    if settings.provider == "ollama":
        return OllamaClient(settings)
    if settings.provider == "openai_compat":
        return OpenAICompatClient(settings)
    raise ValueError(f"unknown provider {settings.provider!r}")
