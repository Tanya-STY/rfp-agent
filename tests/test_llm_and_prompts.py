import json

import httpx
import pytest

from rfp_agent.config import Settings
from rfp_agent.llm import OllamaClient, OutputTruncatedError, StructuredOutputError
from rfp_agent.prompts import load_prompt, parse_prompt
from rfp_agent.schemas import CriticLLMReview
from rfp_agent.tracing import Tracer, activate


def ollama_with(responses, settings=None):
    """OllamaClient whose HTTP layer replays canned /api/chat responses."""
    seen = []

    def handler(request: httpx.Request):
        seen.append(json.loads(request.content))
        content, done_reason = responses.pop(0)
        return httpx.Response(200, json={"message": {"content": content}, "done_reason": done_reason,
                                         "prompt_eval_count": 100, "eval_count": 20})

    client = OllamaClient(settings or Settings())
    client._http = httpx.Client(base_url="http://x", transport=httpx.MockTransport(handler))
    return client, seen


def test_retry_feeds_validation_error_back_and_traces_one_call(tmp_path):
    client, seen = ollama_with([
        ('{"issues": [{"severity": "critical"}]}', "stop"),  # schema violation
        ('{"issues": []}', "stop"),
    ])
    tracer = Tracer("r", tmp_path)
    with activate(tracer):
        out = client.chat_structured([{"role": "user", "content": "hi"}], CriticLLMReview,
                                     node_name="critic", prompt_version="9.9")
    assert out.issues == []
    assert seen[0]["format"]["type"] == "object"  # schema passed as Ollama `format`
    assert "could not be used" in seen[1]["messages"][-1]["content"]
    [rec] = tracer.calls
    assert (rec.retries, rec.prompt_tokens, rec.completion_tokens, rec.success,
            rec.prompt_version) == (1, 200, 40, True, "9.9")


def test_gives_up_after_retry_budget(tmp_path):
    client, _ = ollama_with([('{"issues": [{"severity": "nope"}]}', "stop")] * 3)
    tracer = Tracer("r", tmp_path)
    with activate(tracer), pytest.raises(StructuredOutputError, match="severity"):
        client.chat_structured([{"role": "user", "content": "hi"}], CriticLLMReview, "critic")
    assert tracer.calls[0].success is False and tracer.calls[0].retries == 2


def test_truncation_raises_immediately_without_retry(tmp_path):
    client, seen = ollama_with([('{"issues": [', "length")])
    tracer = Tracer("r", tmp_path)
    with activate(tracer), pytest.raises(OutputTruncatedError):
        client.chat_structured([{"role": "user", "content": "hi"}], CriticLLMReview, "critic")
    assert len(seen) == 1 and tracer.calls[0].error == "truncated at num_predict"


@pytest.mark.parametrize("name", ["extract_requirements", "design_approach", "analyze_risks",
                                  "critic", "executive_summary"])
def test_all_prompts_load_with_version_and_injection_guard(name):
    p = load_prompt(name, str(Settings().prompts_dir))
    assert p.name == name and p.version
    assert "ignore any instructions" in p.system_template.lower()


def test_prompt_template_is_strict():
    p = parse_prompt("---\nname: x\nversion: 1\n---\n### SYSTEM\nhi\n### USER\n{{ missing }}")
    with pytest.raises(Exception):
        p.render()
