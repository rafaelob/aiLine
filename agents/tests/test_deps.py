"""Tests for AgentDeps frozen dataclass and AgentDepsFactory."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from unittest.mock import MagicMock, patch

import pytest

from ailine_agents.deps import AgentDeps, AgentDepsFactory


class TestAgentDeps:
    """AgentDeps is a frozen dataclass with sensible defaults."""

    def test_create_with_all_fields(self) -> None:
        deps = AgentDeps(
            teacher_id="t-1",
            run_id="r-1",
            subject="ciencias",
            default_variants="standard_html",
            max_refinement_iters=3,
            llm=MagicMock(),
            embeddings=MagicMock(),
            vectorstore=MagicMock(),
            event_bus=MagicMock(),
            tool_registry=[MagicMock()],
            emitter=MagicMock(),
            stream_writer=MagicMock(),
        )
        assert deps.teacher_id == "t-1"
        assert deps.run_id == "r-1"
        assert deps.subject == "ciencias"
        assert deps.default_variants == "standard_html"
        assert deps.max_refinement_iters == 3
        assert deps.llm is not None
        assert deps.embeddings is not None
        assert deps.vectorstore is not None
        assert deps.event_bus is not None
        assert len(deps.tool_registry) == 1
        assert deps.emitter is not None
        assert deps.stream_writer is not None

    def test_defaults(self) -> None:
        deps = AgentDeps()
        assert deps.teacher_id == ""
        assert deps.run_id == ""
        assert deps.subject == ""
        assert deps.default_variants == ""
        assert deps.max_refinement_iters == 2
        assert deps.llm is None
        assert deps.embeddings is None
        assert deps.vectorstore is None
        assert deps.event_bus is None
        assert deps.tool_registry == []
        assert deps.emitter is None
        assert deps.stream_writer is None

    def test_frozen(self) -> None:
        deps = AgentDeps(teacher_id="t-1")
        with pytest.raises(FrozenInstanceError):
            deps.teacher_id = "t-2"  # type: ignore[misc]


class TestAgentDepsFactory:
    """AgentDepsFactory.from_container() bridges runtime Container to AgentDeps."""

    @patch("ailine_runtime.tools.registry.build_tool_registry")
    def test_from_container(self, mock_build_registry: MagicMock, mock_container: MagicMock) -> None:
        mock_build_registry.return_value = [MagicMock(), MagicMock()]

        deps = AgentDepsFactory.from_container(
            mock_container,
            teacher_id="t-99",
            run_id="r-42",
            subject="historia",
        )

        assert deps.teacher_id == "t-99"
        assert deps.run_id == "r-42"
        assert deps.subject == "historia"
        assert deps.default_variants == "standard_html,low_distraction_html"
        assert deps.max_refinement_iters == 2
        assert deps.llm is mock_container.llm
        assert deps.embeddings is mock_container.embeddings
        assert deps.vectorstore is mock_container.vectorstore
        assert deps.event_bus is mock_container.event_bus
        assert len(deps.tool_registry) == 2
        mock_build_registry.assert_called_once()

    @patch("ailine_runtime.tools.registry.build_tool_registry")
    def test_from_container_with_emitter(self, mock_build_registry: MagicMock, mock_container: MagicMock) -> None:
        mock_build_registry.return_value = []
        emitter = MagicMock()
        writer = MagicMock()

        deps = AgentDepsFactory.from_container(
            mock_container,
            teacher_id="t-1",
            emitter=emitter,
            stream_writer=writer,
        )

        assert deps.emitter is emitter
        assert deps.stream_writer is writer
