"""Tests for FINDING-16: FakeLLM scenario scripting via response_map."""

from __future__ import annotations

import json

from ailine_runtime.adapters.llm.fake_llm import FakeChatLLM


class TestFakeLLMResponseMap:
    async def test_response_map_keyword_match(self):
        llm = FakeChatLLM(
            response_map={
                "plan": '{"type": "plan_response"}',
                "refine": '{"type": "refine_response"}',
                "execute": '{"type": "execute_response"}',
            }
        )
        messages = [{"role": "user", "content": "Create a plan for math class"}]
        result = await llm.generate(messages)
        assert json.loads(result) == {"type": "plan_response"}

    async def test_response_map_case_insensitive(self):
        llm = FakeChatLLM(response_map={"PLAN": "matched"})
        messages = [{"role": "user", "content": "create a plan"}]
        result = await llm.generate(messages)
        assert result == "matched"

    async def test_response_map_no_match_falls_to_responses_list(self):
        llm = FakeChatLLM(
            responses=["fallback"],
            response_map={"plan": "plan_response"},
        )
        messages = [{"role": "user", "content": "something unrelated"}]
        result = await llm.generate(messages)
        assert result == "fallback"

    async def test_response_map_no_match_no_responses_falls_to_deterministic(self):
        llm = FakeChatLLM(response_map={"plan": "plan_response"})
        messages = [{"role": "user", "content": "something unrelated"}]
        result = await llm.generate(messages)
        # Falls through to deterministic JSON generator
        parsed = json.loads(result)
        assert "title" in parsed

    async def test_response_map_increments_call_count(self):
        llm = FakeChatLLM(response_map={"plan": "matched"})
        messages = [{"role": "user", "content": "make a plan"}]
        assert llm._call_count == 0
        await llm.generate(messages)
        assert llm._call_count == 1

    async def test_response_map_with_stream(self):
        llm = FakeChatLLM(response_map={"plan": "streamed-plan"})
        messages = [{"role": "user", "content": "create a plan"}]
        chunks = []
        async for chunk in llm.stream(messages):
            chunks.append(chunk)
        assert "".join(chunks) == "streamed-plan"

    async def test_response_map_first_keyword_wins(self):
        llm = FakeChatLLM(
            response_map={
                "plan": "plan_wins",
                "aula": "aula_wins",
            }
        )
        messages = [{"role": "user", "content": "create a plan de aula"}]
        result = await llm.generate(messages)
        # "plan" is checked first, so it should match
        assert result == "plan_wins"

    async def test_empty_response_map_behaves_as_before(self):
        llm = FakeChatLLM(response_map={})
        messages = [{"role": "user", "content": "Fracoes"}]
        result = await llm.generate(messages)
        parsed = json.loads(result)
        assert "title" in parsed

    async def test_backward_compatible_responses_list(self):
        """Existing responses list behavior is unchanged."""
        llm = FakeChatLLM(responses=["resp1", "resp2"])
        messages = [{"role": "user", "content": "anything"}]
        assert await llm.generate(messages) == "resp1"
        assert await llm.generate(messages) == "resp2"
        assert await llm.generate(messages) == "resp1"
