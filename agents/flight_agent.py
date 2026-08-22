"""
agents/flight_agent.py
======================
Sub-Agent process that handles flight booking tasks.
"""
import sys
import os
import json
import httpx

# Ensure we can import from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mock_armoriq.client import ArmorIQClient

MCP_URL = "http://localhost:8001/tools/call"

def execute_tool(tool_name: str, args: dict) -> dict:
    resp = httpx.post(MCP_URL, json={"tool_name": tool_name, "args": args})
    return resp.json()

def main():
    print("✈️  [Flight Agent] Booting up...")
    
    # 1. Initialize its own client with its own keypair
    agent_client = ArmorIQClient(agent_id="agent-flight-001")
    
    # 2. Read delegated token
    try:
        with open("tokens.json", "r") as f:
            tokens = json.load(f)
            my_token = tokens["flight_agent"]
    except Exception as e:
        print("❌ [Flight Agent] Error reading token:", e)
        return

    # 3. Perform work using SDK invoke()
    try:
        # Search flights
        res1 = agent_client.invoke(
            token=my_token,
            tool_name="search_flights",
            args={"origin": "BOM", "destination": "DEL"},
            execute_fn=execute_tool
        )
        flight_id = res1["flights"][0]["id"]
        
        # Book flight
        agent_client.invoke(
            token=my_token,
            tool_name="book_flight",
            args={"flight_id": flight_id, "passenger_name": "Hackathon Judge"},
            execute_fn=execute_tool
        )
    except PermissionError:
        pass # blocked, handled in invoke

if __name__ == "__main__":
    main()
