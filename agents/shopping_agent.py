"""
agents/shopping_agent.py
======================
Sub-Agent process that handles shopping tasks.
Demonstrates scope violation and TTL expiry.
"""
import sys
import os
import time
import json
import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mock_armoriq.client import ArmorIQClient

MCP_URL = "http://localhost:8003/tools/call"

def execute_tool(tool_name: str, args: dict) -> dict:
    resp = httpx.post(MCP_URL, json={"tool_name": tool_name, "args": args})
    return resp.json()

def main():
    print("[Shopping Agent] Booting up...")
    agent_client = ArmorIQClient(agent_id="agent-shopping-003")
    
    try:
        with open("tokens.json", "r") as f:
            my_token = json.load(f)["shopping_agent"]
    except Exception as e:
        print("[Shopping Agent] Error reading token:", e)
        return

    # 1. Valid action: search
    try:
        res1 = agent_client.invoke(
            token=my_token,
            tool_name="search_items",
            args={"query": "headphones"},
            execute_fn=execute_tool
        )
        
        # 2. Valid action: add to cart
        item_id = res1["results"][0]["id"]
        agent_client.invoke(
            token=my_token,
            tool_name="add_to_cart",
            args={"item_id": item_id, "qty": 1},
            execute_fn=execute_tool
        )
        
        # 3. INVALID action: attempt checkout (Scope Violation Demo)
        print("[Shopping Agent] Attempting to checkout (this should be blocked!)...")
        agent_client.invoke(
            token=my_token,
            tool_name="checkout",
            args={"cart_id": "cart-99"},
            execute_fn=execute_tool
        )
    except PermissionError:
        print("[Shopping Agent] Checkout was blocked as expected.")

    # 4. EXPIRED action: wait for TTL to expire and try again (Token Expiry Demo)
    ttl_delay = int(os.getenv("SHOPPING_AGENT_TTL", "10")) + 1
    print(f"[Shopping Agent] Waiting {ttl_delay} seconds to demo token expiry...")
    time.sleep(ttl_delay)
    
    try:
        print("[Shopping Agent] Attempting another search (should be expired!)...")
        agent_client.invoke(
            token=my_token,
            tool_name="search_items",
            args={"query": "cable"},
            execute_fn=execute_tool
        )
    except PermissionError:
        print("[Shopping Agent] Token expired as expected.")

if __name__ == "__main__":
    main()
