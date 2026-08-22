"""
agents/calendar_agent.py
======================
Sub-Agent process that handles calendar management tasks.
"""
import sys
import os
import json
import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mock_armoriq.client import ArmorIQClient

MCP_URL = "http://localhost:8002/tools/call"

def execute_tool(tool_name: str, args: dict) -> dict:
    resp = httpx.post(MCP_URL, json={"tool_name": tool_name, "args": args})
    return resp.json()

def main():
    print("📅 [Calendar Agent] Booting up...")
    agent_client = ArmorIQClient(agent_id="agent-calendar-002")
    
    try:
        with open("tokens.json", "r") as f:
            my_token = json.load(f)["calendar_agent"]
    except Exception as e:
        print("❌ [Calendar Agent] Error reading token:", e)
        return

    try:
        res1 = agent_client.invoke(
            token=my_token,
            tool_name="read_events",
            args={"day": "Thursday"},
            execute_fn=execute_tool
        )
        
        # Find conflict
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
        pass

if __name__ == "__main__":
    main()
