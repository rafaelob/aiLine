from __future__ import annotations

from typing import Protocol

from .evidence_pack import EvidencePack


class WebSearchTool(Protocol):
    def search(self, query: str, top_k: int = 6) -> EvidencePack: ...


class RAGManager:
    """Wrapper that normalizes external retrieval into EvidencePacks."""
    def __init__(self, web_search: WebSearchTool | None = None) -> None:
        self.web_search = web_search

    def search_web(self, query: str, top_k: int = 6) -> EvidencePack:
        if self.web_search is None:
            return EvidencePack(query=query, items=[], coverage_gaps=["web_search tool not configured"])
        return self.web_search.search(query=query, top_k=top_k)
