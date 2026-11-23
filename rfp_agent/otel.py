"""Optional OpenTelemetry export of a run, viewable in Arize Phoenix (or any OTLP backend).

Off unless ``RFP_OTEL_ENDPOINT`` is set, e.g. ``http://localhost:6006/v1/traces`` for a
local ``phoenix serve``. The JSONL trace stays the source of truth (dashboard, evals,
cost report); this bridge mirrors it as spans:

    run <id>                      (CHAIN)
    ├── extract_requirements      (CHAIN, one per graph node execution)
    │   ├── chat qwen2.5:7b       (LLM: tokens, latency, prompt version, retries)
    │   └── embed nomic-embed-text (EMBEDDING)
    └── ...

Attribute names follow the OpenInference conventions Phoenix understands
(``openinference.span.kind``, ``llm.model_name``, ``llm.token_count.*``).
It is fed from exactly two places in ``tracing.py``: ``span()`` and ``Tracer.add_call``.
"""

from __future__ import annotations

import time
from typing import Any


class OTelBridge:
    def __init__(self, run_id: str, endpoint: str | None = None, exporter: Any = None):
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor

        self.provider = TracerProvider(resource=Resource.create(
            {"service.name": "rfp-agent", "openinference.project.name": "rfp-agent"}))
        if exporter is None:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            # Batch processor exports on a background thread: an unreachable collector
            # retries there and never slows the pipeline (a synchronous processor
            # blocked each span for ~7 s of retries when Phoenix was down).
            self.provider.add_span_processor(BatchSpanProcessor(
                OTLPSpanExporter(endpoint=endpoint, timeout=2), schedule_delay_millis=1000,
                export_timeout_millis=3000))
        else:  # tests: in-memory exporter, synchronous so spans are visible at once
            self.provider.add_span_processor(SimpleSpanProcessor(exporter))
        self.tracer = self.provider.get_tracer("rfp_agent")
        self.root = self.tracer.start_span(f"run {run_id}", attributes={
            "openinference.span.kind": "CHAIN", "rfp.run_id": run_id})
        self.stack: list[Any] = []

    def _ctx(self):
        from opentelemetry.trace import set_span_in_context
        return set_span_in_context(self.stack[-1] if self.stack else self.root)

    def start_node(self, node: str, attrs: dict[str, Any]) -> None:
        span = self.tracer.start_span(node, context=self._ctx(), attributes={
            "openinference.span.kind": "CHAIN",
            **{f"rfp.{k}": str(v) for k, v in attrs.items()}})
        self.stack.append(span)

    def end_node(self, status: str) -> None:
        from opentelemetry.trace import Status, StatusCode
        if not self.stack:
            return
        span = self.stack.pop()
        if status != "ok":
            span.set_status(Status(StatusCode.ERROR, status))
        span.end()

    def llm_call(self, rec: Any) -> None:
        from opentelemetry.trace import Status, StatusCode
        end = time.time_ns()
        start = end - int(rec.latency_ms * 1e6)
        kind = "LLM" if rec.kind == "chat" else "EMBEDDING"
        span = self.tracer.start_span(f"{rec.kind} {rec.model}", context=self._ctx(),
                                      start_time=start, attributes={
            "openinference.span.kind": kind,
            "llm.model_name": rec.model,
            "llm.token_count.prompt": rec.prompt_tokens,
            "llm.token_count.completion": rec.completion_tokens,
            "llm.token_count.total": rec.prompt_tokens + rec.completion_tokens,
            "rfp.node": rec.node,
            "rfp.prompt_version": rec.prompt_version,
            "rfp.retries": rec.retries,
            "rfp.cost_usd": rec.cost_usd,
        })
        if not rec.success:
            span.set_status(Status(StatusCode.ERROR, rec.error or "error"))
        span.end(end_time=end)

    def close(self) -> None:
        while self.stack:
            self.end_node("ok")
        self.root.end()
        self.provider.force_flush(timeout_millis=3000)
        self.provider.shutdown()
