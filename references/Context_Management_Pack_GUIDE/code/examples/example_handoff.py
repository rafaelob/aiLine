"""Example: Dual handoff contracts (delegate vs transfer).

Run:
  python example_handoff.py

This is framework-agnostic. In your runtime, you'd serialize these contracts
into whatever your vendor/framework expects (OpenAI handoffs, ADK transfer_to_agent,
LangGraph routing, etc.).
"""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from context_manager import make_handoff_package


def main():
    # 1) Delegate: manager retains control; calls a specialist as a tool/subroutine.
    delegate_pkg = make_handoff_package(
        from_agent="orchestrator",
        to_agent="security_reviewer",
        objective="Review a PR diff for security issues and propose fixes.",
        constraints=[
            "Do not change public APIs without justification",
            "Flag risky auth/crypto patterns",
            "Return structured findings",
        ],
        state={
            "decisions": ["We must keep backwards compatibility"],
            "facts": ["Repo uses OAuth2"],
            "preferences": ["Prefer minimal diffs"],
            "todos": ["Ship by Friday"],
        },
        handoff_mode="delegate",
        delegate_input={
            "task": "review_diff",
            "artifact": {"uri": "s3://acme/prs/123/diff.patch", "sha256": "..."},
            "expected_output_schema": "review_findings_v1",
        },
        budget_hint={"max_input_tokens": 40000, "priority": "high"},
    )

    # 2) Transfer: route control to a specialist agent that will talk directly to the user.
    transfer_pkg = make_handoff_package(
        from_agent="triage",
        to_agent="billing_support",
        objective="Handle billing issues directly with the user.",
        constraints=["Be polite", "Ask clarifying questions when needed"],
        state={
            "decisions": [],
            "facts": ["User is on enterprise plan"],
            "preferences": ["Prefer email follow-up"],
            "todos": ["Collect invoice ID"],
        },
        handoff_mode="transfer",
        context_policy={
            "history_mode": "filtered",
            "max_history_tokens": 12000,
            "include_slices": ["STATE_JSON", "RECENT_DIALOG"],
            "exclude_slices": ["RAW_TOOL_DUMPS"],
            "redaction": {"pii": True, "secrets": True},
        },
        budget_hint={"max_input_tokens": 60000, "priority": "high"},
    )

    print("\n=== DELEGATE (agents-as-tools) ===")
    print(delegate_pkg)
    print("\n=== TRANSFER (control handoff) ===")
    print(transfer_pkg)


if __name__ == "__main__":
    main()
