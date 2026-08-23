"""
agents/custom_flight_agent.py
=============================
Customizable Flight Agent that reads configuration from GUI
"""
import sys
import os
import json
import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mock_armoriq.client import ArmorIQClient

MCP_URL = "http://localhost:8001/tools/call"

def execute_tool(tool_name: str, args: dict) -> dict:
    resp = httpx.post(MCP_URL, json={"tool_name": tool_name, "args": args})
    return resp.json()

def main():
    print("[Custom Flight Agent] Starting with GUI configuration...")
    
    # Load custom config if available
    config_path = "custom_config.json"
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
        
        flight_config = config["agents"]["flight"]
        custom_args = flight_config["args"]
        print(f"[Custom Flight Agent] Using custom route: {custom_args['origin']} -> {custom_args['destination']}")
        print(f"[Custom Flight Agent] Passenger: {custom_args['passenger_name']}")
    else:
        # Fallback to defaults
        custom_args = {"origin": "NYC", "destination": "LAX", "passenger_name": "Default User"}
    
    # Initialize client
    agent_client = ArmorIQClient(agent_id="agent-flight-gui")
    
    # Read token
    try:
        with open("tokens.json", "r") as f:
            tokens = json.load(f)
            my_token = tokens.get("flight_agent") or tokens.get("flight")
    except Exception as e:
        print(f"[Custom Flight Agent] Error reading token: {e}")
        return

    # Execute flight operations
    try:
        # Search flights with custom parameters
        print(f"[Custom Flight Agent] Searching flights: {custom_args['origin']} -> {custom_args['destination']}")
        search_result = agent_client.invoke(
            token=my_token,
            tool_name="search_flights",
            args={"origin": custom_args["origin"], "destination": custom_args["destination"]},
            execute_fn=execute_tool
        )
        
        if "flights" in search_result and search_result["flights"]:
            flight_id = search_result["flights"][0]["id"]
            print(f"[Custom Flight Agent] Found flight: {flight_id}")
            
            # Book the flight
            print(f"[Custom Flight Agent] Booking flight for {custom_args['passenger_name']}")
            booking_result = agent_client.invoke(
                token=my_token,
                tool_name="book_flight",
                args={"flight_id": flight_id, "passenger_name": custom_args["passenger_name"]},
                execute_fn=execute_tool
            )
            
            print("[Custom Flight Agent] Successfully completed booking!")
            
    except PermissionError as e:
        print(f"[Custom Flight Agent] Permission denied: {e}")
    except Exception as e:
        print(f"[Custom Flight Agent] Error: {e}")

if __name__ == "__main__":
    main()