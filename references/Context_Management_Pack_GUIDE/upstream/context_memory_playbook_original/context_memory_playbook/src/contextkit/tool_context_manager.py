from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .token_count import TokenCounter
from .util.json_redact import redact


@dataclass
class ArtifactStore:
    """Armazena payloads grandes fora do contexto do modelo (handle)."""

    artifacts_dir: Path

    def write(self, tool_name: str, payload: Any) -> str:
        safe_payload = redact(payload)
        is_structured = isinstance(safe_payload, (dict, list))
        raw = (
            json.dumps(safe_payload, ensure_ascii=False, indent=2)
            if is_structured
            else str(safe_payload)
        )
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
        ext = "json" if is_structured else "txt"
        path = self.artifacts_dir / f"{tool_name}_{digest}.{ext}"
        path.write_text(raw, encoding="utf-8")
        return str(path)


@dataclass
class ToolContextManager:
    token_counter: TokenCounter
    artifact_store: ArtifactStore
    max_inline_chars: int = 50_000

    def _compact_text(self, text: str, head: int = 2_800, tail: int = 1_000) -> str:
        text = text or ""
        if len(text) <= head + tail + 50:
            return text
        return text[:head] + "\n\n… (truncado) …\n\n" + text[-tail:]

    def summarize(
        self,
        tool_name: str,
        payload: Any,
        *,
        is_error: bool = False,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Retorna um resumo seguro para inserir no prompt (com handle opcional)."""

        safe_payload = redact(payload)

        # Serializa.
        if isinstance(safe_payload, (dict, list)):
            raw = json.dumps(safe_payload, ensure_ascii=False, indent=2)
        else:
            raw = str(safe_payload)

        handle: Optional[str] = None
        inline = raw

        if len(raw) > self.max_inline_chars:
            handle = self.artifact_store.write(tool_name, payload)
            inline = self._compact_text(raw)

        # Heurística de salient facts (sem LLM).
        salient: list[str] = []
        caveats: list[str] = []

        if isinstance(safe_payload, dict):
            keys = list(safe_payload.keys())
            salient.append(f"objeto com {len(keys)} chaves: {', '.join(keys[:12])}{'…' if len(keys) > 12 else ''}")
            # Flag de erro comum
            if any(k.lower() in ("error", "errors", "exception") for k in keys):
                caveats.append("payload contém campos de erro; verifique status e mensagens")
        elif isinstance(safe_payload, list):
            salient.append(f"lista com {len(safe_payload)} itens")
        else:
            salient.append(f"texto com {len(raw)} chars")

        status = "error" if is_error else "success"
        lines: list[str] = [
            "## TOOL_RESULT_SUMMARY",
            f"- tool: {tool_name}",
            f"- status: {status}",
        ]
        if handle:
            lines.append(f"- handle: {handle}")
        lines.append("- salient_facts:")
        lines.extend([f"  - {s}" for s in salient] or ["  - (none)"])
        if caveats:
            lines.append("- caveats:")
            lines.extend([f"  - {c}" for c in caveats])
        lines.append("\n### payload_excerpt\n")
        lines.append(inline)

        out = "\n".join(lines).strip()

        if max_tokens is None:
            return out

        # Enforce max_tokens.
        if self.token_counter.count_text(out) <= max_tokens:
            return out

        # Trim excerpt first.
        # Find payload section and shorten it progressively.
        # Simples: manter cabeçalho e cortar no final.
        char_budget = int(max_tokens * self.token_counter.chars_per_token)
        if len(out) <= char_budget:
            return out
        head = int(char_budget * 0.8)
        tail = char_budget - head
        return out[:head] + "\n\n… (tool summary truncado por budget) …\n\n" + out[-tail:]
