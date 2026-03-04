#!/usr/bin/env python3
"""
Fetch a small set of GitHub reference files (public) into references/.

This script is OPTIONAL. It requires internet access.
"""
from __future__ import annotations

from pathlib import Path
from urllib.request import urlopen, Request

ROOT = Path(__file__).resolve().parents[1]
REFS = ROOT / "references"
REFS.mkdir(parents=True, exist_ok=True)


def fetch_raw(owner: str, repo: str, path: str, ref: str = "main") -> str:
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}"
    req = Request(url, headers={"User-Agent": "contextkit-refresh/0.1"})
    with urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def write(name: str, content: str) -> Path:
    path = REFS / name
    path.write_text(content, encoding="utf-8")
    return path


def main() -> None:
    targets = [
        # Claude Code
        ("claude_code_README.md", ("anthropics", "claude-code", "README.md", "main")),
        ("claude_code_CHANGELOG.md", ("anthropics", "claude-code", "CHANGELOG.md", "main")),
        # OpenAI Codex
        ("openai_codex_README.md", ("openai", "codex", "README.md", "main")),
    ]

    for fname, (owner, repo, path, ref) in targets:
        try:
            content = fetch_raw(owner, repo, path, ref)
            out = write(fname, content)
            print(f"OK  {owner}/{repo}:{path}@{ref} -> {out}")
        except Exception as e:
            print(f"ERR {owner}/{repo}:{path}@{ref}: {e}")


if __name__ == "__main__":
    main()
