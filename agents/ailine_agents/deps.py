"""Agent dependency injection — bridges hexagonal Container into Pydantic AI RunContext.

AgentDeps is the single data structure flowing through RunContext[AgentDeps],
giving all agents type-safe access to ports (LLM, embeddings, vectorstore, etc.),
tenant context, SSE streaming, and the tool registry.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ailine_runtime.api.streaming.events import SSEEvent, SSEEventEmitter
    from ailine_runtime.domain.ports.embeddings import Embeddings
    from ailine_runtime.domain.ports.events import EventBus
    from ailine_runtime.domain.ports.llm import ChatLLM
    from ailine_runtime.domain.ports.vectorstore import VectorStore
    from ailine_runtime.shared.container import Container
    from ailine_runtime.tools.registry import ToolDef


@dataclass(frozen=True)
class AgentDeps:
    """Dependencies injected into every Pydantic AI agent via RunContext[AgentDeps].

    Maps 1:1 with the hexagonal port protocols from the runtime layer.
    """

    teacher_id: str = ""
    run_id: str = ""
    subject: str = ""
    default_variants: str = ""
    max_refinement_iters: int = 2

    # Port implementations
    llm: ChatLLM | None = None
    embeddings: Embeddings | None = None
    vectorstore: VectorStore | None = None
    event_bus: EventBus | None = None

    # Tool registry
    tool_registry: list[ToolDef] = field(default_factory=list)

    # SSE streaming (only in streaming context)
    emitter: SSEEventEmitter | None = None
    stream_writer: Callable[[SSEEvent], None] | None = None


class AgentDepsFactory:
    """Builds AgentDeps from the runtime Container + request context."""

    @staticmethod
    def from_container(
        container: Container,
        *,
        teacher_id: str,
        run_id: str = "",
        subject: str = "",
        default_variants: str | None = None,
        max_refinement_iters: int | None = None,
        emitter: Any = None,
        stream_writer: Any = None,
    ) -> AgentDeps:
        from ailine_runtime.tools.registry import build_tool_registry

        settings = container.settings
        return AgentDeps(
            teacher_id=teacher_id,
            run_id=run_id,
            subject=subject,
            default_variants=default_variants or settings.default_variants,
            max_refinement_iters=(
                max_refinement_iters
                if max_refinement_iters is not None
                else settings.max_refinement_iters
            ),
            llm=container.llm,
            embeddings=container.embeddings,
            vectorstore=container.vectorstore,
            event_bus=container.event_bus,
            tool_registry=build_tool_registry(),
            emitter=emitter,
            stream_writer=stream_writer,
        )
