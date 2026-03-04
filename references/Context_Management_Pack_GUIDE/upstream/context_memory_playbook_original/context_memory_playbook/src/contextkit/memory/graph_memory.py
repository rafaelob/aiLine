from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class Node:
    id: str
    type: str
    label: str
    props: dict[str, Any]
    source: str
    ts: int
    confidence: float
    ttl_days: Optional[int] = None


@dataclass
class Edge:
    src: str
    dst: str
    type: str
    props: dict[str, Any]
    source: str
    ts: int
    confidence: float
    ttl_days: Optional[int] = None


class GraphMemoryStore:
    """SQLite-backed graph store (nodes + edges) with provenance & TTL.

    This is intentionally minimal and dependency-free.
    """
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._conn = sqlite3.connect(str(db_path))
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._init_schema()

    def close(self) -> None:
        self._conn.close()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS nodes (
              id TEXT PRIMARY KEY,
              type TEXT NOT NULL,
              label TEXT NOT NULL,
              props_json TEXT NOT NULL,
              source TEXT NOT NULL,
              ts INTEGER NOT NULL,
              confidence REAL NOT NULL,
              ttl_days INTEGER
            );
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS edges (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              src TEXT NOT NULL,
              dst TEXT NOT NULL,
              type TEXT NOT NULL,
              props_json TEXT NOT NULL,
              source TEXT NOT NULL,
              ts INTEGER NOT NULL,
              confidence REAL NOT NULL,
              ttl_days INTEGER
            );
            """
        )
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_src ON edges(src);")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges(dst);")
        self._conn.commit()

    @staticmethod
    def _is_expired(ts: int, ttl_days: Optional[int]) -> bool:
        if ttl_days is None:
            return False
        return (time.time() - ts) > (ttl_days * 86400)

    def upsert_node(self, node: Node) -> None:
        self._conn.execute(
            """
            INSERT INTO nodes (id, type, label, props_json, source, ts, confidence, ttl_days)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              type=excluded.type,
              label=excluded.label,
              props_json=excluded.props_json,
              source=excluded.source,
              ts=excluded.ts,
              confidence=excluded.confidence,
              ttl_days=excluded.ttl_days;
            """,
            (
                node.id,
                node.type,
                node.label,
                json.dumps(node.props, ensure_ascii=False),
                node.source,
                node.ts,
                node.confidence,
                node.ttl_days,
            ),
        )
        self._conn.commit()

    def add_edge(self, edge: Edge) -> None:
        self._conn.execute(
            """
            INSERT INTO edges (src, dst, type, props_json, source, ts, confidence, ttl_days)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                edge.src,
                edge.dst,
                edge.type,
                json.dumps(edge.props, ensure_ascii=False),
                edge.source,
                edge.ts,
                edge.confidence,
                edge.ttl_days,
            ),
        )
        self._conn.commit()

    def find_nodes_by_label(self, query: str, limit: int = 10) -> list[Node]:
        q = f"%{query.lower()}%"
        rows = self._conn.execute(
            "SELECT id, type, label, props_json, source, ts, confidence, ttl_days FROM nodes WHERE lower(label) LIKE ? LIMIT ?",
            (q, limit),
        ).fetchall()
        out: list[Node] = []
        for r in rows:
            node = Node(
                id=r[0],
                type=r[1],
                label=r[2],
                props=json.loads(r[3]),
                source=r[4],
                ts=int(r[5]),
                confidence=float(r[6]),
                ttl_days=r[7],
            )
            if not self._is_expired(node.ts, node.ttl_days):
                out.append(node)
        return out

    def get_neighbors(self, node_id: str, limit: int = 50) -> list[Edge]:
        rows = self._conn.execute(
            "SELECT src, dst, type, props_json, source, ts, confidence, ttl_days FROM edges WHERE src=? OR dst=? LIMIT ?",
            (node_id, node_id, limit),
        ).fetchall()
        out: list[Edge] = []
        for r in rows:
            e = Edge(
                src=r[0],
                dst=r[1],
                type=r[2],
                props=json.loads(r[3]),
                source=r[4],
                ts=int(r[5]),
                confidence=float(r[6]),
                ttl_days=r[7],
            )
            if not self._is_expired(e.ts, e.ttl_days):
                out.append(e)
        return out

    def get_subgraph(self, seed_ids: list[str], max_hops: int = 2, max_nodes: int = 50) -> tuple[list[Node], list[Edge]]:
        """Bounded BFS expansion."""
        seen: set[str] = set()
        frontier: list[str] = list(seed_ids)
        nodes: dict[str, Node] = {}
        edges: list[Edge] = []

        # Load seed nodes
        for sid in seed_ids:
            row = self._conn.execute(
                "SELECT id, type, label, props_json, source, ts, confidence, ttl_days FROM nodes WHERE id=?",
                (sid,),
            ).fetchone()
            if row:
                n = Node(
                    id=row[0],
                    type=row[1],
                    label=row[2],
                    props=json.loads(row[3]),
                    source=row[4],
                    ts=int(row[5]),
                    confidence=float(row[6]),
                    ttl_days=row[7],
                )
                if not self._is_expired(n.ts, n.ttl_days):
                    nodes[n.id] = n

        hop = 0
        while frontier and hop < max_hops and len(nodes) < max_nodes:
            next_frontier: list[str] = []
            for nid in frontier:
                if nid in seen:
                    continue
                seen.add(nid)
                for e in self.get_neighbors(nid):
                    edges.append(e)
                    other = e.dst if e.src == nid else e.src
                    if other not in nodes and len(nodes) < max_nodes:
                        row = self._conn.execute(
                            "SELECT id, type, label, props_json, source, ts, confidence, ttl_days FROM nodes WHERE id=?",
                            (other,),
                        ).fetchone()
                        if row:
                            n = Node(
                                id=row[0],
                                type=row[1],
                                label=row[2],
                                props=json.loads(row[3]),
                                source=row[4],
                                ts=int(row[5]),
                                confidence=float(row[6]),
                                ttl_days=row[7],
                            )
                            if not self._is_expired(n.ts, n.ttl_days):
                                nodes[n.id] = n
                                next_frontier.append(n.id)
            frontier = next_frontier
            hop += 1

        return list(nodes.values()), edges

    @staticmethod
    def summarize(nodes: list[Node], edges: list[Edge], max_items: int = 25) -> str:
        """Convert a subgraph into a compact context slice."""
        out: list[str] = ["## GRAPH_MEMORY_SLICE"]
        if not nodes:
            out.append("(empty)")
            return "\n".join(out)

        out.append("### Entidades")
        for n in nodes[:max_items]:
            out.append(f"- {n.type}:{n.id} — {n.label} (conf={n.confidence:.2f}, src={n.source})")

        out.append("\n### Relações")
        for e in edges[:max_items]:
            out.append(f"- {e.src} -[{e.type}]-> {e.dst} (conf={e.confidence:.2f}, src={e.source})")

        return "\n".join(out)


    def slice_for_query(
        self,
        query: str,
        *,
        max_seed_nodes: int = 5,
        max_hops: int = 1,
        max_nodes: int = 30,
        max_items: int = 25,
    ) -> str:
        """Atalho: busca nós por label e retorna um slice resumido do subgrafo.

        Útil para:
          - recuperar memória relevante com pouco código,
          - empacotar no tool budget (Y−X).
        """
        seeds = self.find_nodes_by_label(query, limit=max_seed_nodes)
        if not seeds:
            return "## GRAPH_MEMORY_SLICE\n(empty)"
        nodes, edges = self.subgraph([n.id for n in seeds], max_hops=max_hops, max_nodes=max_nodes)
        return self.summarize(nodes, edges, max_items=max_items)
