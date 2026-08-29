"""
agents/calendar_agent.py
========================
Sub-Agent process that handles calendar management tasks.
MCP servers are mocked inline so no localhost connection is needed.
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mock_armoriq.client import ArmorIQClient

# ── Inline mock — no MCP server needed ───────────────────────────────
def execute_tool(tool_name: str, args: dict) -> dict:
    """Mock tool execution — simulates MCP server responses locally."""
    if tool_name == "read_events":
        return {
            "events": [
                {"id": "evt-001", "title": "CONFLICT: Old Stand-up", "day": args.get("day", "Thursday")},
                {"id": "evt-002", "title": "Lunch", "day": args.get("day", "Thursday")}
            ]
        }
    elif tool_name == "delete_event":
        return {"deleted": args.get("event_id"), "status": "DELETED"}
    elif tool_name == "create_event":
        return {"event_id": "evt-new", "title": args.get("title"), "status": "CREATED"}
    return {"status": "ok", "tool": tool_name}


def main():
    print("[Calendar Agent] Booting up...")
    agent_client = ArmorIQClient(agent_id="agent-calendar-002")

    # Resolve token file relative to project root (not cwd)
    if os.environ.get("VERCEL"):
        token_file = "/tmp/tokens.json"
    else:
        token_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tokens.json")
    try:
        with open(token_file, "r") as f:
            my_token = json.load(f)["calendar_agent"]
    except Exception as e:
        print(f"[Calendar Agent] Error reading token: {e}")
        return

    try:
        res1 = agent_client.invoke(
            token=my_token,
            tool_name="read_events",
            args={"day": "Thursday"},
            execute_fn=execute_tool
        )

        conflict_id = None
        for evt in res1.get("events", []):
            if "CONFLICT" in evt["title"]:
                conflict_id = evt["id"]
                break

        if conflict_id:
            agent_client.invoke(
                token=my_token,
                tool_name="delete_event",
                args={"event_id": conflict_id},
                execute_fn=execute_tool
            )
    except PermissionError:
        pass  # blocked — already logged in invoke()
    except Exception as e:
        print(f"[Calendar Agent] Unexpected error: {e}")


if __name__ == "__main__":
    main()
