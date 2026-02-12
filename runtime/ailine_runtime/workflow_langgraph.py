"""Legacy entry point — delegates to workflow.plan_workflow.

Kept for backward compatibility with api_app.py imports.
"""

from __future__ import annotations

from typing import Any

from .workflow.plan_workflow import RunState, build_plan_workflow


def build_workflow(cfg: Any, registry: list[Any]):
    """Build workflow (legacy signature)."""
    return build_plan_workflow(cfg, registry)


__all__ = ["RunState", "build_workflow"]
