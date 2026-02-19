from __future__ import annotations

import json
import os
import re
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# -----------------------------
# Local material store (MVP)
# -----------------------------
#
# Objetivo: permitir um demo funcional de "documentos do professor" sem dependências pesadas.
# - Em produção: substituir por Postgres + pgvector + pipeline de ingestão.
# - Aqui: armazenamos materiais como JSON + texto e fazemos busca simples por tokens.
#
# Store layout:
#   .local_store/
#     materials/
#       {teacher_id}/
#         {subject_slug}/
#           {material_id}.json
#
# Each material json:
#   {
#     "material_id": "...",
#     "teacher_id": "...",
#     "subject": "Matemática",
#     "title": "...",
#     "tags": ["frações", "bncc:EF04MA07"],
#     "content": "...texto...",
#     "created_at": "2026-02-11T..."
#   }
#


def _root_dir() -> Path:
    return Path(os.getenv("AILINE_LOCAL_STORE", ".local_store"))


def _materials_dir() -> Path:
    d = _root_dir() / "materials"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _slug(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9\-\_\s]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s or "subject"


@dataclass(frozen=True)
class Material:
    material_id: str
    teacher_id: str
    subject: str
    title: str
    tags: list[str]
    content: str
    created_at: str


def add_material(
    *,
    teacher_id: str,
    subject: str,
    title: str,
    content: str,
    tags: list[str] | None = None,
    created_at: str | None = None,
) -> Material:
    from ..shared.sanitize import safe_path_component

    # Defense-in-depth: validate path components even though the API layer
    # validates teacher_id format.  Prevents directory traversal if a store
    # function is ever called outside of the HTTP request path.
    safe_path_component(teacher_id, label="teacher_id")

    material_id = str(uuid.uuid4())
    tags = tags or []
    created_at = created_at or datetime.now(UTC).isoformat()

    m = Material(
        material_id=material_id,
        teacher_id=teacher_id,
        subject=subject,
        title=title,
        tags=tags,
        content=content,
        created_at=created_at,
    )

    out_dir = _materials_dir() / teacher_id / _slug(subject)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{material_id}.json"
    out_path.write_text(
        json.dumps(m.__dict__, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return m


def load_material(
    material_id: str, *, teacher_id: str | None = None, subject: str | None = None
) -> Material | None:
    # Busca simples por varredura (MVP). Em produção: lookup por índice/DB.
    for m in iter_materials(teacher_id=teacher_id, subject=subject):
        if m.material_id == material_id:
            return m
    return None


def iter_materials(
    *, teacher_id: str | None = None, subject: str | None = None
) -> Iterable[Material]:
    root = _materials_dir()
    teacher_dirs = (
        [root / teacher_id] if teacher_id else [p for p in root.iterdir() if p.is_dir()]
    )

    for tdir in teacher_dirs:
        if not tdir.exists():
            continue
        subj_dirs = (
            [tdir / _slug(subject)]
            if subject
            else [p for p in tdir.iterdir() if p.is_dir()]
        )
        for sdir in subj_dirs:
            if not sdir.exists():
                continue
            for f in sdir.glob("*.json"):
                try:
                    raw = json.loads(f.read_text(encoding="utf-8"))
                    yield Material(**raw)
                except (json.JSONDecodeError, ValueError, TypeError, OSError):
                    continue


# -----------------------------
# Simple text search (token overlap)
# -----------------------------

_STOP = {
    # pt
    "a",
    "o",
    "os",
    "as",
    "um",
    "uma",
    "uns",
    "umas",
    "de",
    "da",
    "do",
    "das",
    "dos",
    "e",
    "é",
    "em",
    "no",
    "na",
    "nos",
    "nas",
    "para",
    "por",
    "com",
    "sem",
    "que",
    "como",
    "se",
    "ao",
    "à",
    "às",
    "aos",
    "ou",
    "não",
    "sim",
    "mais",
    "menos",
    "muito",
    "pouco",
    "sobre",
    "entre",
    "também",
    "já",
    "há",
    "ser",
    "estar",
    "ter",
    "foi",
    "era",
    "são",
    "sua",
    "seu",
    "suas",
    "seus",
    # en
    "the",
    "an",
    "and",
    "or",
    "to",
    "of",
    "in",
    "on",
    "for",
    "with",
    "without",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "it",
}


def _tokens(text: str) -> list[str]:
    text = text.lower()
    parts = re.findall(r"[\w\-]+", text)
    return [p for p in parts if p and p not in _STOP and len(p) >= 2]


def _chunk_text(text: str, max_chars: int = 900) -> list[str]:
    # split por parágrafos e agrupa; quebra parágrafos longos que excedam max_chars
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    buf = ""
    for p in paras:
        # Split paragraphs longer than max_chars into max_chars-sized pieces
        while len(p) > max_chars:
            chunks.append(p[:max_chars])
            p = p[max_chars:]
        if not p:  # pragma: no cover — defensive: while loop always leaves >=1 char
            continue
        if len(buf) + len(p) + 2 <= max_chars:
            buf = (buf + "\n\n" + p).strip()
        else:
            if buf:
                chunks.append(buf)
            buf = p
    if buf:
        chunks.append(buf)
    if not chunks:
        chunks = [text[:max_chars] if text else text]
    return chunks


def search_materials(
    *,
    query: str,
    k: int = 5,
    teacher_id: str | None = None,
    subject: str | None = None,
    material_ids: list[str] | None = None,
    tags: list[str] | None = None,
) -> list[dict[str, Any]]:
    q_tokens = _tokens(query)
    if not q_tokens:
        return []

    id_filter = set(material_ids or [])
    tag_filter = {t.lower() for t in (tags or [])}

    scored: list[dict[str, Any]] = []
    for m in iter_materials(teacher_id=teacher_id, subject=subject):
        if id_filter and m.material_id not in id_filter:
            continue
        if tag_filter:
            mt = {t.lower() for t in m.tags}
            if not (mt & tag_filter):
                continue

        chunks = _chunk_text(m.content)
        for idx, ch in enumerate(chunks):
            ch_low = ch.lower()
            score = sum(1 for t in q_tokens if t in ch_low)
            if score <= 0:
                continue
            scored.append(
                {
                    "score": score,
                    "material_id": m.material_id,
                    "title": m.title,
                    "subject": m.subject,
                    "chunk_index": idx,
                    "text": ch[:1200],
                    "tags": m.tags,
                }
            )

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[: max(1, min(k, 20))]
