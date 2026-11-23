"""Minimal, centralised tracing.

All observability flows through two entry points:

* ``record_call(...)`` - called by every LLM client (and the embedder) once per logical
  call. It captures run_id, node, prompt_version, model, token counts, latency,
  retries and success/error.
* ``span(node)`` - context manager around each graph node (start/end/duration).

Both append JSON lines to ``runs/<run_id>/trace.jsonl``. The active tracer is held in a
``ContextVar`` so the LLM client never needs a tracer argument, and so a later phase
can add an OpenTelemetry / Arize Phoenix exporter in exactly one place
(``Tracer._emit``) without touching agents.
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

_current_tracer: ContextVar["Tracer | None"] = ContextVar("current_tracer", default=None)
_current_node: ContextVar[str] = ContextVar("current_node", default="-")


@dataclass
class CallRecord:
    run_id: str
    node: str
    kind: str  # "chat" | "embed"
    model: str
    prompt_version: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    retries: int
    success: bool
    error: str | None = None
    cost_usd: float = 0.0
    extra: dict[str, Any] = field(default_factory=dict)


class Tracer:
    def __init__(self, run_id: str, run_dir: Path):
        self.run_id = run_id
        self.run_dir = run_dir
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.path = run_dir / "trace.jsonl"
        self.calls: list[CallRecord] = []
        self.spans: list[dict[str, Any]] = []
        self.otel: Any = None  # optional OTelBridge (rfp_agent/otel.py), see enable_otel

    def enable_otel(self, endpoint: str | None = None, exporter: Any = None) -> None:
        """Mirror this run to OpenTelemetry (Phoenix). Never fatal: tracing must not
        break a run, so a missing package or unreachable endpoint only logs a warning."""
        try:
            from .otel import OTelBridge
            self.otel = OTelBridge(self.run_id, endpoint=endpoint, exporter=exporter)
        except Exception as exc:  # noqa: BLE001
            import logging
            logging.getLogger("rfp_agent").warning("OpenTelemetry export disabled: %s", exc)

    def _otel(self, method: str, *args: Any) -> None:
        if self.otel is None:
            return
        try:
            getattr(self.otel, method)(*args)
        except Exception as exc:  # noqa: BLE001
            import logging
            logging.getLogger("rfp_agent").warning("OpenTelemetry export failed: %s", exc)
            self.otel = None

    def close(self) -> None:
        self._otel("close")

    # -- sinks -------------------------------------------------------------------------
    def _emit(self, event: dict[str, Any]) -> None:
        event = {"ts": datetime.now(timezone.utc).isoformat(), "run_id": self.run_id, **event}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, default=str) + "\n")

    def add_call(self, rec: CallRecord) -> None:
        self.calls.append(rec)
        self._emit({"type": "llm_call", **asdict(rec)})
        self._otel("llm_call", rec)

    def event(self, name: str, **data: Any) -> None:
        """Free-form event (e.g. dedupe stats, routing decisions)."""
        self._emit({"type": "event", "name": name, "node": _current_node.get(), **data})

    # -- aggregation for CLI / metadata --------------------------------------------------
    def summary_by_node(self) -> dict[str, dict[str, float]]:
        agg: dict[str, dict[str, float]] = defaultdict(
            lambda: {"calls": 0, "embed_calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "latency_ms": 0.0,
                     "retries": 0, "errors": 0, "cost_usd": 0.0}
        )
        for c in self.calls:
            a = agg[c.node]
            a["calls" if c.kind == "chat" else "embed_calls"] += 1
            a["prompt_tokens"] += c.prompt_tokens
            a["completion_tokens"] += c.completion_tokens
            a["latency_ms"] += c.latency_ms
            a["retries"] += c.retries
            a["errors"] += 0 if c.success else 1
            a["cost_usd"] += c.cost_usd
        return dict(agg)

    def totals(self) -> dict[str, float]:
        tot = {"calls": 0, "embed_calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "latency_ms": 0.0,
               "retries": 0, "errors": 0, "cost_usd": 0.0}
        for row in self.summary_by_node().values():
            for k in tot:
                tot[k] += row[k]
        return tot


@contextmanager
def activate(tracer: Tracer) -> Iterator[Tracer]:
    token = _current_tracer.set(tracer)
    try:
        yield tracer
    finally:
        _current_tracer.reset(token)


def current_tracer() -> Tracer | None:
    return _current_tracer.get()


@contextmanager
def span(node: str, **attrs: Any) -> Iterator[None]:
    """Wrap a graph node: emits span_start / span_end with duration."""
    tracer = _current_tracer.get()
    token = _current_node.set(node)
    start = time.perf_counter()
    if tracer:
        tracer._emit({"type": "span_start", "node": node, **attrs})
        tracer._otel("start_node", node, attrs)
    status = "ok"
    try:
        yield
    except Exception as exc:  # noqa: BLE001 - re-raised, recorded for the trace
        status = f"error: {type(exc).__name__}: {exc}"
        raise
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        if tracer:
            rec = {"type": "span_end", "node": node, "duration_ms": round(duration_ms, 1),
                   "status": status}
            tracer.spans.append(rec)
            tracer._emit(rec)
            tracer._otel("end_node", status)
        _current_node.reset(token)


def record_call(
    *,
    node: str | None,
    kind: str,
    model: str,
    prompt_version: str,
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: float,
    retries: int,
    success: bool,
    error: str | None = None,
    price_input_per_1m: float = 0.0,
    price_output_per_1m: float = 0.0,
    **extra: Any,
) -> CallRecord:
    """The single hook every model call goes through. Safe to call with no tracer."""
    tracer = _current_tracer.get()
    cost = (prompt_tokens * price_input_per_1m + completion_tokens * price_output_per_1m) / 1e6
    rec = CallRecord(
        run_id=tracer.run_id if tracer else "-",
        node=node or _current_node.get(),
        kind=kind,
        model=model,
        prompt_version=prompt_version,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        latency_ms=round(latency_ms, 1),
        retries=retries,
        success=success,
        error=error,
        cost_usd=cost,
        extra=extra,
    )
    if tracer:
        tracer.add_call(rec)
    return rec
