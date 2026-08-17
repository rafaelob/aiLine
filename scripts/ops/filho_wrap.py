#!/usr/bin/env python3
# FLEET-TEMPLATE v2026.08.47 — instalado por fleet_install.py; fonte: ~/.claude/fleet-template/
"""Run one command as a Fleet FILHO: PARENT set, leaked AGENT stripped.

Usage:
  python filho_wrap.py --parent A -- python -c "..."
  python filho_wrap.py --  cmd   # parent from FLEET_AGENT_ID of this process
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

import _mural_ident as ident  # noqa: E402
from _no_console import apply_no_console  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="filho_wrap")
    ap.add_argument("--parent", default="", help="letra do pai (default: FLEET_AGENT_ID desta sessão)")
    ap.add_argument("comando", nargs=argparse.REMAINDER)
    args = ap.parse_args(argv)
    cmd = list(args.comando)
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        print("filho_wrap: falta o comando depois de --", file=sys.stderr)
        return 2
    pai = (args.parent or os.environ.get(ident.ENV_AGENTE) or "").strip()
    try:
        env = ident.ambiente_para_filho(pai, os.environ)
    except ident.IdentError as exc:
        print(f"filho_wrap: {exc}", file=sys.stderr)
        return 2
    opcoes = {"env": env, "check": False}
    apply_no_console(opcoes)
    return subprocess.run(cmd, **opcoes).returncode


if __name__ == "__main__":
    raise SystemExit(main())
