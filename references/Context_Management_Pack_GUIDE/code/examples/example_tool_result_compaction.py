"""
Example: compact a tool result into digest+pointer.

Run:
  python example_tool_result_compaction.py
"""
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from context_manager import BlobStore, compact_tool_result

def fake_summarizer(text: str) -> str:
    # Replace with an LLM call in production.
    # This is deterministic and intentionally simplistic.
    lines = text.splitlines()
    head = "\n".join(lines[:20])
    return "DIGEST:\n" + head

def main():
    blob = BlobStore()

    raw = "\n".join([f"row {i}: value={i*i}" for i in range(5000)])
    out = compact_tool_result(
        tool_name="db_query_orders",
        raw_result=raw,
        budget_tokens=2000,
        summarizer=fake_summarizer,
        blob_store=blob,
    )
    print(out["mode"])
    print("pointer:", out.get("pointer"))
    print("summary tokens est:", out.get("tokens_summary_est"))

if __name__ == "__main__":
    main()
