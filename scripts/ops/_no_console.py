#!/usr/bin/env python3
# FLEET-TEMPLATE v2026.08.47 — instalado por fleet_install.py; fonte: ~/.claude/fleet-template/
"""Windows flags so Fleet children never allocate a console window.

A windowless parent (pythonw, a hook, a hidden agent shell) that starts
``git.exe`` / ``git.cmd`` without ``CREATE_NO_WINDOW`` gets a new ``conhost``
and steals focus. Measured on this machine: ``Git\\cmd\\git.exe`` is a CUI
launcher. The numeric fallback keeps the flag if ``subprocess`` is patched.
"""
from __future__ import annotations

import os
import subprocess

_CREATE_NO_WINDOW = 0x08000000
_CREATE_NEW_CONSOLE = 0x00000010
_DETACHED_PROCESS = 0x00000008


def no_console_kwargs() -> dict[str, int]:
    """Return ``creationflags=CREATE_NO_WINDOW`` on Windows; empty elsewhere."""
    if os.name != "nt":
        return {}
    flag = getattr(subprocess, "CREATE_NO_WINDOW", _CREATE_NO_WINDOW)
    if not isinstance(flag, int) or isinstance(flag, bool) or flag <= 0:
        flag = _CREATE_NO_WINDOW
    return {"creationflags": flag}


def apply_no_console(kw: dict) -> dict:
    """OR ``CREATE_NO_WINDOW`` into *kw* unless a new/detached console was asked."""
    if os.name != "nt":
        return kw
    new_console = getattr(subprocess, "CREATE_NEW_CONSOLE", _CREATE_NEW_CONSOLE)
    detached = getattr(subprocess, "DETACHED_PROCESS", _DETACHED_PROCESS)
    no_window = getattr(subprocess, "CREATE_NO_WINDOW", _CREATE_NO_WINDOW)
    if not isinstance(no_window, int) or isinstance(no_window, bool) or no_window <= 0:
        no_window = _CREATE_NO_WINDOW
    flags = int(kw.get("creationflags", 0) or 0)
    if not flags & (new_console | detached):
        kw["creationflags"] = flags | no_window
    return kw
