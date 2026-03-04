"""
Example: assemble slices with a budget profile.

Run:
  python example_budgeted_assembly.py
"""
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from context_manager import BudgetManager, ContextAssembler, ContextLedger, Slice

def main():
    bm = BudgetManager.from_yaml("../../configs/budget_profiles.yaml")
    # Try swapping profiles:
    # - tool_heavy_350k
    # - continuous_tool_heavy_400k_steady_240k
    Y, budgets, profile = bm.compute_budgets("continuous_tool_heavy_400k_steady_240k")

    ledger = ContextLedger()
    assembler = ContextAssembler(budgets, ledger=ledger)

    slices = [
        Slice("SYSTEM_DEV","system_dev","system","[SYSTEM+DEV kernel...]",priority=0,score=1.0, trusted=True),
        Slice("STATE_JSON","state_json","system","{...state json...}",priority=1,score=1.0, trusted=True),
        Slice("HISTORY_RECENT","history_recency","user","(recent turns...)",priority=5,score=0.5, trusted=True),
        Slice("TOOL_RESULT_RAW","tool_results","tool","(huge tool output...)",priority=6,score=0.4, trusted=False),
        Slice("RAG_EVIDENCE","rag_evidence","system","(evidence pack...)",priority=6,score=0.6, trusted=False),
    ]

    selected, used = assembler.select(slices)
    msgs = assembler.to_messages(selected)

    print("Profile:", profile.name)
    print("window_tokens:", profile.window_tokens)
    print("reserve_output_tokens:", profile.reserve_output_tokens)
    print("safety_margin_tokens:", profile.safety_margin_tokens)
    print("utilization_target_ratio:", profile.utilization_target_ratio)
    print("Y_total_input (effective):", Y)
    print("Used:", used)
    print("Messages:")
    for m in msgs:
        print("-", m["role"], ":", m["content"][:80].replace("\n"," ") + ("..." if len(m["content"])>80 else ""))

    print("\nLedger events:", len(ledger.events))

if __name__ == "__main__":
    main()
