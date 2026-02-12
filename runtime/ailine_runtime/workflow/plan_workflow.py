"""Plan generation workflow — re-exports from ailine_agents.

This module maintains backward compatibility for existing imports.
The actual implementation now lives in ailine_agents.workflows.plan_workflow.
"""

from __future__ import annotations

# Re-export state types
from ailine_agents.workflows._state import RunState

# Re-export workflow builder
from ailine_agents.workflows.plan_workflow import (
    DEFAULT_RECURSION_LIMIT,
    build_plan_workflow,
)

__all__ = [
    "DEFAULT_RECURSION_LIMIT",
    "RunState",
    "build_plan_workflow",
]
