"""Tests for AgentDeps frozen dataclass and AgentDepsFactory."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from unittest.mock import MagicMock, patch

import pytest

from ailine_agents.deps import AgentDeps, AgentDepsFactory
from ailine_agents.resilience import CircuitBreaker


class TestAgentDeps:
    """AgentDeps is a frozen dataclass with sensible defaults."""

    def test_create_with_all_fields(self) -> None:
        cb = CircuitBreaker()
        deps = AgentDeps(
            teacher_id="t-1",
            run_id="r-1",
            subject="ciencias",
            default_variants="standard_html",
            max_refinement_iters=3,
            max_workflow_duration_seconds=600,
            llm=MagicMock(),
            embeddings=MagicMock(),
            vectorstore=MagicMock(),
            event_bus=MagicMock(),
            tool_registry=[MagicMock()],
            emitter=MagicMock(),
            stream_writer=MagicMock(),
            circuit_breaker=cb,
        )
        assert deps.teacher_id == "t-1"
        assert deps.run_id == "r-1"
        assert deps.subject == "ciencias"
        assert deps.default_variants == "standard_html"
        assert deps.max_refinement_iters == 3
        assert deps.max_workflow_duration_seconds == 600
        assert deps.llm is not None
        assert deps.embeddings is not None
        assert deps.vectorstore is not None
        assert deps.event_bus is not None
        assert len(deps.tool_registry) == 1
        assert deps.emitter is not None
        assert deps.stream_writer is not None
        assert deps.circuit_breaker is cb

    def test_defaults(self) -> None:
        deps = AgentDeps()
        assert deps.teacher_id == ""
        assert deps.run_id == ""
        assert deps.subject == ""
        assert deps.default_variants == ""
        assert deps.max_refinement_iters == 2
        assert deps.max_workflow_duration_seconds == 300
        assert deps.llm is None
        assert deps.embeddings is None
        assert deps.vectorstore is None
        assert deps.event_bus is None
        assert deps.tool_registry == []
        assert deps.emitter is None
        assert deps.stream_writer is None
        assert isinstance(deps.circuit_breaker, CircuitBreaker)

    def test_frozen(self) -> None:
        deps = AgentDeps(teacher_id="t-1")
        with pytest.raises(FrozenInstanceError):
            deps.teacher_id = "t-2"  # type: ignore[misc]

    def test_circuit_breaker_mutable_through_frozen(self) -> None:
        """Circuit breaker is a mutable object held by reference in the frozen dataclass."""
        deps = AgentDeps(teacher_id="t-1")
        # Can mutate the circuit breaker even though deps is frozen
        deps.circuit_breaker.record_failure()
        assert deps.circuit_breaker.failure_count == 1
        deps.circuit_breaker.record_success()
        assert deps.circuit_breaker.failure_count == 0


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
        assert deps.max_workflow_duration_seconds == 300
        assert deps.llm is mock_container.llm
        assert deps.embeddings is mock_container.embeddings
        assert deps.vectorstore is mock_container.vectorstore
        assert deps.event_bus is mock_container.event_bus
        assert len(deps.tool_registry) == 2
        assert isinstance(deps.circuit_breaker, CircuitBreaker)
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

    @patch("ailine_runtime.tools.registry.build_tool_registry")
    def test_from_container_shared_circuit_breaker(
        self, mock_build_registry: MagicMock, mock_container: MagicMock,
    ) -> None:
        """All deps from the same factory share the same circuit breaker."""
        mock_build_registry.return_value = []

        deps1 = AgentDepsFactory.from_container(mock_container, teacher_id="t-1")
        deps2 = AgentDepsFactory.from_container(mock_container, teacher_id="t-2")

        assert deps1.circuit_breaker is deps2.circuit_breaker

    @patch("ailine_runtime.tools.registry.build_tool_registry")
    def test_from_container_custom_timeout(
        self, mock_build_registry: MagicMock, mock_container: MagicMock,
    ) -> None:
        mock_build_registry.return_value = []

        deps = AgentDepsFactory.from_container(
            mock_container,
            teacher_id="t-1",
            max_workflow_duration_seconds=120,
        )

        assert deps.max_workflow_duration_seconds == 120
