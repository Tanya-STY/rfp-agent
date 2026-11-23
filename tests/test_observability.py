"""Phase 3: OpenTelemetry mirror of the JSONL trace, and the hosted-cost report."""

from rfp_agent.costs import hosted_cost, render_markdown, run_costs
from rfp_agent.tracing import Tracer, activate, record_call, span


def test_otel_bridge_mirrors_nodes_and_llm_calls(tmp_path):
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    exp = InMemorySpanExporter()
    t = Tracer("r1", tmp_path / "r1")
    t.enable_otel(exporter=exp)
    with activate(t):
        with span("extract_requirements"):
            record_call(node=None, kind="chat", model="qwen2.5:7b", prompt_version="1.4.0",
                        prompt_tokens=100, completion_tokens=20, latency_ms=50, retries=0,
                        success=True)
        with span("critic"):
            record_call(node=None, kind="chat", model="qwen2.5:7b", prompt_version="1.0.0",
                        prompt_tokens=10, completion_tokens=5, latency_ms=5, retries=1,
                        success=False, error="bad json")
    t.close()
    spans = {s.name: s for s in exp.get_finished_spans()}
    assert set(spans) == {"run r1", "extract_requirements", "critic", "chat qwen2.5:7b"}
    assert len(exp.get_finished_spans()) == 5
    llm = [s for s in exp.get_finished_spans() if s.name == "chat qwen2.5:7b"]
    assert llm[0].attributes["llm.token_count.prompt"] == 100
    assert llm[0].attributes["openinference.span.kind"] == "LLM"
    assert llm[0].parent.span_id == spans["extract_requirements"].context.span_id
    assert spans["extract_requirements"].parent.span_id == spans["run r1"].context.span_id
    assert not llm[1].status.is_ok


def test_otel_failure_never_breaks_a_run(tmp_path):
    class Broken:
        def export(self, spans):
            raise RuntimeError("collector down")

        def shutdown(self):
            pass

    t = Tracer("r2", tmp_path / "r2")
    t.enable_otel(exporter=Broken())
    with activate(t), span("extract_requirements"):
        record_call(node=None, kind="chat", model="m", prompt_version="1", prompt_tokens=1,
                    completion_tokens=1, latency_ms=1, retries=0, success=True)
    t.close()
    assert len(t.calls) == 1 and (tmp_path / "r2" / "trace.jsonl").exists()


def test_cost_report_from_trace(tmp_path):
    t = Tracer("r3", tmp_path / "r3")
    with activate(t), span("extract_requirements"):
        record_call(node=None, kind="chat", model="m", prompt_version="1",
                    prompt_tokens=1_000_000, completion_tokens=200_000, latency_ms=60_000,
                    retries=0, success=True)
        record_call(node=None, kind="embed", model="e", prompt_version="-", prompt_tokens=5,
                    completion_tokens=0, latency_ms=1, retries=0, success=True)
    r = run_costs(tmp_path / "r3")
    assert r["total"]["calls"] == 1  # embeddings are not counted as chat calls
    assert hosted_cost(1_000_000, 200_000, "Claude Haiku 5.5") == r["hosted"]["Claude Haiku 5.5"]
    assert abs(r["hosted"]["Claude Haiku 5.5"] - 0.20) < 1e-9
    assert "| r3 | 1 | 1,000,000 | 200,000 | 1.0 | $0.200 |" in render_markdown([r])
