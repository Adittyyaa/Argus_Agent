"""
agents/flight_agent.py
======================
Sub-Agent process that handles flight booking tasks.
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
    if tool_name == "search_flights":
        return {
            "flights": [
                {"id": "FL-001", "origin": args.get("origin", "BOM"),
                 "destination": args.get("destination", "DEL"),
                 "price": 4500, "airline": "IndiGo"}
            ]
        }
    elif tool_name == "book_flight":
        return {
            "booking_id": "BK-9821",
            "flight_id": args.get("flight_id"),
            "passenger": args.get("passenger_name", "Passenger"),
            "status": "CONFIRMED"
        }
    return {"status": "ok", "tool": tool_name}


def main():
    print("[Flight Agent] Booting up...")
    agent_client = ArmorIQClient(agent_id="agent-flight-001")

    # Read delegated token
    token_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tokens.json")
    try:
        with open(token_file, "r") as f:
            my_token = json.load(f)["flight_agent"]
    except Exception as e:
        print(f"[Flight Agent] Error reading token: {e}")
        return

    try:
        res1 = agent_client.invoke(
            token=my_token,
            tool_name="search_flights",
            args={"origin": "BOM", "destination": "DEL"},
            execute_fn=execute_tool
        )
        flight_id = res1["flights"][0]["id"]

        agent_client.invoke(
            token=my_token,
            tool_name="book_flight",
            args={"flight_id": flight_id, "passenger_name": "Hackathon Judge"},
            execute_fn=execute_tool
        )
    except PermissionError:
        pass  # blocked — already logged in invoke()
    except Exception as e:
        print(f"[Flight Agent] Unexpected error: {e}")


if __name__ == "__main__":
    main()
