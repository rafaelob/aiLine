from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .token_count import TokenCounter


@dataclass(frozen=True)
class MCPServerConfig:
    """Config de um servidor MCP.

    Observação:
      - Campos concretos podem variar por stack (OpenAI vs clients próprios).
      - Mantenha `extra` para extensões sem quebrar compatibilidade.
    """
    server_label: str
    server_url: str
    allowed_tools: Optional[list[str]] = None
    require_approval: Optional[str] = None  # ex.: "always"|"never"|"auto" (depende do provedor)
    authorization: Optional[dict] = None
    extra: dict = field(default_factory=dict)


@dataclass(frozen=True)
class MCPToolMeta:
    name: str
    description: str
    server_label: Optional[str] = None


class MCPRegistry:
    """Registro mínimo de MCP servers + catálogo de tools (para discovery).

    Padrão estado‑da‑arte:
      - manter catálogo mínimo (name+description)
      - filtrar allowlist na origem quando possível
      - carregar schema apenas sob demanda
    """

    def __init__(self, token_counter: TokenCounter) -> None:
        self.token_counter = token_counter
        self._servers: dict[str, MCPServerConfig] = {}
        self._tools: list[MCPToolMeta] = []

    def add_server(self, cfg: MCPServerConfig) -> None:
        self._servers[cfg.server_label] = cfg

    def list_servers(self) -> list[MCPServerConfig]:
        return list(self._servers.values())

    def register_tool(self, tool: MCPToolMeta) -> None:
        self._tools.append(tool)

    def list_tools(self) -> list[MCPToolMeta]:
        return sorted(self._tools, key=lambda t: (t.server_label or "", t.name))

    def build_tool_catalog_snippet(self, max_tokens: int) -> str:
        """Catálogo compacto (para incluir no tool budget)."""
        lines: list[str] = [
            "## MCP_TOOL_CATALOG",
            "(catálogo mínimo; carregue schemas sob demanda)",
            "",
        ]
        for t in self.list_tools():
            prefix = f"[{t.server_label}] " if t.server_label else ""
            lines.append(f"- {prefix}{t.name}: {t.description}")
        text = "\n".join(lines).strip()

        if self.token_counter.count_text(text) <= max_tokens:
            return text

        # Trim por budget.
        trimmed = lines[:3]
        for line in lines[3:]:
            cand = "\n".join(trimmed + [line])
            if self.token_counter.count_text(cand) > max_tokens:
                break
            trimmed.append(line)
        trimmed.append("\n(… catálogo MCP truncado por budget …)")
        return "\n".join(trimmed).strip()

    def to_openai_tools(self) -> list[dict]:
        """Gera definições de tools para stacks que suportam MCP nativamente (ex.: OpenAI).

        Retorna algo do tipo:
          {"type": "mcp", "server_label": ..., "server_url": ..., ...}

        Atenção: confirme os campos exatos na doc do provedor (podem mudar).
        """
        tools: list[dict] = []
        for s in self.list_servers():
            d: dict = {
                "type": "mcp",
                "server_label": s.server_label,
                "server_url": s.server_url,
            }
            if s.allowed_tools is not None:
                d["allowed_tools"] = s.allowed_tools
            if s.require_approval is not None:
                d["require_approval"] = s.require_approval
            if s.authorization is not None:
                d["authorization"] = s.authorization
            if s.extra:
                d.update(s.extra)
            tools.append(d)
        return tools
