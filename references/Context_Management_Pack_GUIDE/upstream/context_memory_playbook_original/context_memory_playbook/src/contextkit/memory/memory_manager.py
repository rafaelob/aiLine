from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Optional

from .graph_memory import GraphMemoryStore, Node, Edge


@dataclass
class MemoryWriteCandidate:
    scope: str  # user|project|org
    kind: str   # preference|decision|relation|note
    payload: dict[str, Any]
    source: str
    confidence: float = 0.7
    ttl_days: Optional[int] = 180
    requires_confirmation: bool = True


class MemoryManager:
    """High-level memory manager (policy + stores).

    - Uses GraphMemoryStore for relations.
    - You can extend it with vector store / text notes as needed.
    """
    def __init__(self, graph_store: GraphMemoryStore) -> None:
        self.graph = graph_store

    def propose_write(self, candidate: MemoryWriteCandidate) -> MemoryWriteCandidate:
        """Hook point for policy checks (PII, stability, etc.)."""
        # Minimal policy: always require confirmation unless explicitly disabled.
        return candidate

    def apply_write(self, candidate: MemoryWriteCandidate) -> None:
        """Persist a confirmed memory candidate."""
        ts = int(time.time())
        kind = candidate.kind

        if kind == "preference":
            # Expect payload: {user_id, key, value}
            user_id = str(candidate.payload["user_id"])
            key = str(candidate.payload["key"])
            value = str(candidate.payload["value"])
            pref_id = f"pref:{user_id}:{key}"
            self.graph.upsert_node(
                Node(
                    id=pref_id,
                    type="Preference",
                    label=f"{key}={value}",
                    props={"key": key, "value": value, "scope": candidate.scope},
                    source=candidate.source,
                    ts=ts,
                    confidence=candidate.confidence,
                    ttl_days=candidate.ttl_days,
                )
            )
            self.graph.add_edge(
                Edge(
                    src=f"user:{user_id}",
                    dst=pref_id,
                    type="PREFERS",
                    props={},
                    source=candidate.source,
                    ts=ts,
                    confidence=candidate.confidence,
                    ttl_days=candidate.ttl_days,
                )
            )
            return

        if kind == "relation":
            # Expect payload: {src_id, dst_id, rel_type, src_label?, dst_label?}
            src = str(candidate.payload["src_id"])
            dst = str(candidate.payload["dst_id"])
            rel_type = str(candidate.payload["rel_type"])
            # Ensure nodes exist (best-effort)
            if "src_label" in candidate.payload:
                self.graph.upsert_node(Node(id=src, type="Entity", label=str(candidate.payload["src_label"]), props={}, source=candidate.source, ts=ts, confidence=candidate.confidence, ttl_days=candidate.ttl_days))
            if "dst_label" in candidate.payload:
                self.graph.upsert_node(Node(id=dst, type="Entity", label=str(candidate.payload["dst_label"]), props={}, source=candidate.source, ts=ts, confidence=candidate.confidence, ttl_days=candidate.ttl_days))
            self.graph.add_edge(Edge(src=src, dst=dst, type=rel_type, props={}, source=candidate.source, ts=ts, confidence=candidate.confidence, ttl_days=candidate.ttl_days))
            return

        if kind == "note":
            # Store as node
            note_id = str(candidate.payload.get("id") or f"note:{ts}")
            text = str(candidate.payload.get("text", ""))
            self.graph.upsert_node(Node(id=note_id, type="Note", label=text[:120], props={"text": text}, source=candidate.source, ts=ts, confidence=candidate.confidence, ttl_days=candidate.ttl_days))
            return

        if kind == "decision":
            dec_id = str(candidate.payload.get("id") or f"decision:{ts}")
            title = str(candidate.payload.get("title", "Decision"))
            rationale = str(candidate.payload.get("rationale", ""))
            self.graph.upsert_node(Node(id=dec_id, type="Decision", label=title, props={"rationale": rationale, **candidate.payload}, source=candidate.source, ts=ts, confidence=candidate.confidence, ttl_days=candidate.ttl_days))
            return

        raise ValueError(f"Unknown memory kind: {kind}")
