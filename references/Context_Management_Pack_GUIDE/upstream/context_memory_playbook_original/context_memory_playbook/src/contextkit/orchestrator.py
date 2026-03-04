from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .config import Config
from .context_assembler import ContextAssembler, CoreBuildResult
from .rolling_summary import RollingSummaryManager, LLMClient
from .skills_registry import SkillsRegistry
from .token_count import OptionalTiktokenCounter, TokenCounter
from .types import Turn
from .tool_context_manager import ArtifactStore, ToolContextManager


@dataclass
class OrchestratorState:
    history: list[Turn] = field(default_factory=list)
    rolling_summary: str = ""


class Orchestrator:
    """Orquestrador mínimo (referência) para o padrão X/Y.

    - NÃO executa tools nem chama LLM por padrão.
    - Foca em: montar contexto, aplicar compaction, calcular budgets.
    """

    def __init__(
        self,
        *,
        config: Config,
        system_prompt: str,
        developer_prompt: str,
        llm: Optional[LLMClient],
        skills_dir: Path,
    ) -> None:
        self.config = config
        self.system_prompt = system_prompt
        self.developer_prompt = developer_prompt

        # Token counter (tiktoken opcional).
        self.token_counter: TokenCounter = OptionalTiktokenCounter(model=config.tokenizer_model, fallback_chars_per_token=4.0)

        # Rolling summary.
        self.rolling_summary_manager = RollingSummaryManager(token_counter=self.token_counter, llm=llm)

        # Skills registry.
        self.skills_registry = SkillsRegistry(skills_dir=skills_dir, token_counter=self.token_counter)
        self.skills_registry.discover()

        # Tool artifact store (para payload grande).
        store = ArtifactStore(artifacts_dir=config.storage.artifacts_dir)
        self.tool_context = ToolContextManager(token_counter=self.token_counter, artifact_store=store)

        # Context assembler.
        self.context_assembler = ContextAssembler(
            config=config,
            token_counter=self.token_counter,
            rolling_summary_manager=self.rolling_summary_manager,
        )

        self.state = OrchestratorState()

    def run_turn(
        self,
        *,
        user_text: str,
        durable_instructions: Optional[str] = None,
        active_skill_names: Optional[list[str]] = None,
        tool_blocks: Optional[list[str]] = None,
    ) -> dict:
        """Processa um turno: monta core, calcula tool budget e (opcionalmente) empacota tool context."""
        active_skill_names = active_skill_names or []
        tool_blocks = tool_blocks or []

        # 1) Append user message as a new Turn.
        self.state.history.append(Turn(user={"role": "user", "content": user_text}))

        # 2) Skills index (catálogo mínimo) e skills ativas.
        skills_index = self.skills_registry.build_index_snippet(self.config.skills.skills_index_budget_tokens)
        active_skills: list[str] = []
        for name in active_skill_names:
            active_skills.append(
                self.skills_registry.activate(
                    name,
                    max_tokens=self.config.skills.max_active_skill_tokens,
                    sections=None,
                )
            )

        # 3) Build core with compaction if needed.
        core: CoreBuildResult = self.context_assembler.build_core(
            system_prompt=self.system_prompt,
            developer_prompt=self.developer_prompt,
            durable_instructions=durable_instructions,
            skills_index=skills_index,
            active_skills=active_skills,
            rolling_summary=self.state.rolling_summary,
            history=self.state.history,
        )
        self.state.rolling_summary = core.rolling_summary

        # 4) Compute tool budget.
        Y = self.config.budgets.Y_total_tokens
        tool_budget = max(Y - core.core_tokens, 0)

        # 5) Optionally pack tool context blocks into a full prompt (<= Y).
        full_messages = self.context_assembler.pack_tool_context(
            core_messages=core.messages,
            tool_blocks=tool_blocks,
            max_total_tokens=Y,
        )

        total_tokens = self.token_counter.count_messages(full_messages)

        return {
            "core_messages": core.messages,
            "core_tokens": core.core_tokens,
            "full_messages": full_messages,
            "total_tokens": total_tokens,
            "tool_budget_tokens": tool_budget,
            "turns_compacted": core.turns_compacted,
            "kept_turns": core.kept_turns,
            "rolling_summary": self.state.rolling_summary,
        }

    def close(self) -> None:
        # Nada a fechar aqui (GraphMemoryStore fecha o DB no caller).
        return
