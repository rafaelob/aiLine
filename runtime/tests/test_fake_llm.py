"""Tests for the FakeChatLLM adapter.

Verifies that FakeChatLLM conforms to the ChatLLM protocol,
produces deterministic responses, and supports streaming.
"""

from __future__ import annotations

import json

from ailine_runtime.adapters.llm.fake_llm import FakeChatLLM

# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


def test_fake_llm_model_name() -> None:
    llm = FakeChatLLM(model="test-model")
    assert llm.model_name == "test-model"


def test_fake_llm_default_model_name() -> None:
    llm = FakeChatLLM()
    assert llm.model_name == "fake-llm"


def test_fake_llm_capabilities() -> None:
    llm = FakeChatLLM()
    caps = llm.capabilities
    assert isinstance(caps, dict)
    assert caps["provider"] == "fake"
    assert caps["streaming"] is True
    assert caps["tool_use"] is False
    assert caps["vision"] is False


# ---------------------------------------------------------------------------
# Generate (deterministic response)
# ---------------------------------------------------------------------------


async def test_generate_returns_json_string() -> None:
    llm = FakeChatLLM()
    messages = [{"role": "user", "content": "Crie um plano sobre fracoes"}]
    result = await llm.generate(messages)
    assert isinstance(result, str)
    # Should be valid JSON
    parsed = json.loads(result)
    assert "title" in parsed
    assert "steps" in parsed
    assert "objectives" in parsed


async def test_generate_uses_canned_response() -> None:
    llm = FakeChatLLM(responses=["resposta fixa 1", "resposta fixa 2"])
    messages = [{"role": "user", "content": "Qualquer pergunta"}]

    r1 = await llm.generate(messages)
    assert r1 == "resposta fixa 1"

    r2 = await llm.generate(messages)
    assert r2 == "resposta fixa 2"

    # Cycles back to first
    r3 = await llm.generate(messages)
    assert r3 == "resposta fixa 1"


async def test_generate_call_count() -> None:
    llm = FakeChatLLM()
    messages = [{"role": "user", "content": "test"}]
    assert llm._call_count == 0
    await llm.generate(messages)
    assert llm._call_count == 1
    await llm.generate(messages)
    assert llm._call_count == 2


async def test_generate_deterministic_includes_user_input() -> None:
    llm = FakeChatLLM()
    messages = [{"role": "user", "content": "Fracoes decimais"}]
    result = await llm.generate(messages)
    parsed = json.loads(result)
    # The title should incorporate the user prompt
    assert "Fracoes decimais" in parsed["title"]


async def test_generate_with_empty_messages() -> None:
    llm = FakeChatLLM()
    result = await llm.generate([])
    assert isinstance(result, str)
    parsed = json.loads(result)
    assert "title" in parsed


# ---------------------------------------------------------------------------
# Stream
# ---------------------------------------------------------------------------


async def test_stream_yields_chunks() -> None:
    llm = FakeChatLLM()
    messages = [{"role": "user", "content": "Plano de aula"}]
    chunks = []
    async for chunk in llm.stream(messages):
        chunks.append(chunk)
    assert len(chunks) > 0
    # Reassembled chunks should be the full response
    full = "".join(chunks)
    parsed = json.loads(full)
    assert "title" in parsed


async def test_stream_with_canned_response() -> None:
    llm = FakeChatLLM(responses=["chunk-resposta-teste"])
    messages = [{"role": "user", "content": "test"}]
    chunks = []
    async for chunk in llm.stream(messages):
        chunks.append(chunk)
    assert "".join(chunks) == "chunk-resposta-teste"


async def test_stream_increments_call_count() -> None:
    llm = FakeChatLLM()
    messages = [{"role": "user", "content": "test"}]
    assert llm._call_count == 0
    async for _ in llm.stream(messages):
        pass
    assert llm._call_count == 1


# ---------------------------------------------------------------------------
# Kwargs passthrough (should not error)
# ---------------------------------------------------------------------------


async def test_generate_accepts_kwargs() -> None:
    llm = FakeChatLLM()
    messages = [{"role": "user", "content": "test"}]
    result = await llm.generate(messages, temperature=0.5, max_tokens=1024, top_p=0.9)
    assert isinstance(result, str)


async def test_stream_accepts_kwargs() -> None:
    llm = FakeChatLLM()
    messages = [{"role": "user", "content": "test"}]
    chunks = []
    async for chunk in llm.stream(messages, temperature=0.5, max_tokens=1024):
        chunks.append(chunk)
    assert len(chunks) > 0
