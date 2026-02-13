"""Tutor session management and chat turn execution.

Uses the ChatLLM port (via Container) instead of Claude Agent SDK directly.
This ensures Glass Box visibility and LangGraph checkpointing compatibility (ADR-048).
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..domain.entities.tutor import TutorAgentSpec, TutorSession, TutorTurnOutput
from .builder import load_tutor_spec


def _root_dir() -> Path:
    return Path(os.getenv("AILINE_LOCAL_STORE", ".local_store"))


def _sessions_dir() -> Path:
    d = _root_dir() / "tutor_sessions"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_session(session: TutorSession) -> dict[str, Any]:
    path = _sessions_dir() / f"{session.session_id}.json"
    path.write_text(session.model_dump_json(indent=2, ensure_ascii=False), encoding="utf-8")
    return {"session_id": session.session_id, "stored_at": str(path)}


def load_session(session_id: str) -> TutorSession | None:
    path = _sessions_dir() / f"{session_id}.json"
    if not path.exists():
        return None
    try:
        return TutorSession(**json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return None


def create_session(tutor_id: str) -> TutorSession:
    from uuid_utils import uuid7

    return TutorSession(
        session_id=str(uuid7()),
        tutor_id=tutor_id,
        created_at=datetime.now(UTC).isoformat(),
    )


def _format_history(session: TutorSession, max_turns: int = 8) -> str:
    msgs = session.messages[-max_turns:]
    lines = []
    for m in msgs:
        role = "ALUNO" if m.role == "user" else "TUTOR"
        lines.append(f"{role}: {m.content}")
    return "\n".join(lines)


def _extract_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    if "{" in text and "}" in text:
        start = text.find("{")
        end = text.rfind("}")
        if 0 <= start < end:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                return None
    return None


async def tutor_chat_turn(
    *,
    cfg: Any,
    registry: list[Any] | None = None,
    tutor_id: str,
    session: TutorSession,
    user_message: str,
    llm: Any | None = None,
) -> dict[str, Any]:
    """Run 1 tutoring turn using the ChatLLM port.

    Uses direct Anthropic API tool calling via the ChatLLM adapter
    instead of Claude Agent SDK (ADR-048).
    """
    spec: TutorAgentSpec | None = load_tutor_spec(tutor_id)
    if spec is None:
        raise ValueError(f"TutorAgentSpec not found: {tutor_id}")

    # Resolve LLM from container or parameter
    if llm is None:
        llm_model = getattr(cfg, "executor_model", "claude-opus-4-6")
        getattr(cfg, "anthropic_api_key", "") or ""
        # Try to get from container if available
        container = getattr(cfg, "_container", None)
        if container and hasattr(container, "llm") and container.llm is not None:
            llm = container.llm
        else:
            from ..adapters.llm.fake_llm import FakeChatLLM

            llm = FakeChatLLM(model=llm_model)

    # Update session with user message
    session.append("user", user_message)

    history = _format_history(session)
    schema = TutorTurnOutput.model_json_schema()

    messages = [
        {
            "role": "user",
            "content": (
                f"{spec.persona.system_prompt}\n\n"
                "## Contrato de resposta (obrigatório)\n"
                "Responda SOMENTE com um JSON válido seguindo o schema abaixo.\n"
                "Não inclua markdown fora do JSON.\n"
                f"schema: {json.dumps(schema, ensure_ascii=False)}\n\n"
                "## Histórico (últimos turnos)\n"
                f"{history}\n\n"
                "## Pergunta atual do aluno\n"
                f"{user_message}\n"
            ),
        }
    ]

    full_text = await llm.generate(messages, temperature=0.7, max_tokens=2048)
    parsed = _extract_json(full_text)

    out: TutorTurnOutput | None = None
    if parsed is not None:
        try:
            out = TutorTurnOutput(**parsed)
        except Exception:
            out = None

    # Persist response in session
    session.append("assistant", json.dumps(parsed, ensure_ascii=False) if parsed else full_text)
    save_session(session)

    return {
        "raw_result": full_text,
        "text": full_text,
        "parsed": parsed,
        "validated": out.model_dump() if out else None,
        "session_id": session.session_id,
    }
