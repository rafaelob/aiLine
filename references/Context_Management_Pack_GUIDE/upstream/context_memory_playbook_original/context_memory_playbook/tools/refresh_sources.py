#!/usr/bin/env python3
"""
Refresh external reference files (Agent Skills index, MCP docs pointers, Claude Code/Codex snippets).

This script is OPTIONAL. It requires internet access in your environment.
It uses only the Python standard library.

Usage:
  python tools/refresh_sources.py
"""
from __future__ import annotations

from pathlib import Path
from urllib.request import urlopen, Request

ROOT = Path(__file__).resolve().parents[1]
REFS = ROOT / "references"
REFS.mkdir(parents=True, exist_ok=True)


def fetch(url: str) -> str:
    req = Request(url, headers={"User-Agent": "contextkit-refresh/0.1"})
    with urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def write(name: str, content: str) -> Path:
    path = REFS / name
    path.write_text(content, encoding="utf-8")
    return path


def main() -> None:
    targets = [
        ("agentskills_llms.txt", "https://agentskills.io/llms.txt"),
        ("agentskills_home.html", "https://agentskills.io/home"),
        # You can add more canonical docs here.
    ]

    for fname, url in targets:
        try:
            content = fetch(url)
            path = write(fname, content)
            print(f"OK  {url} -> {path}")
        except Exception as e:
            print(f"ERR {url}: {e}")


if __name__ == "__main__":
    main()
