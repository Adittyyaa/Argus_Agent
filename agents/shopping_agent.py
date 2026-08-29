"""
agents/shopping_agent.py
========================
Sub-Agent process that handles shopping tasks.
Demonstrates scope violation and TTL expiry.
MCP servers are mocked inline so no localhost connection is needed.
"""
import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mock_armoriq.client import ArmorIQClient

# ── Inline mock — no MCP server needed ───────────────────────────────
def execute_tool(tool_name: str, args: dict) -> dict:
    """Mock tool execution — simulates MCP server responses locally."""
    if tool_name == "search_items":
        return {
            "results": [
                {"id": "item-001", "name": "Sony WH-1000XM5", "price": 299.99},
                {"id": "item-002", "name": "Bose QuietComfort 45", "price": 249.99}
            ]
        }
    elif tool_name == "add_to_cart":
        return {"cart_id": "cart-99", "item_id": args.get("item_id"), "status": "ADDED"}
    elif tool_name == "checkout":
        return {"order_id": "ord-001", "status": "PLACED"}
    return {"status": "ok", "tool": tool_name}


def main():
    print("[Shopping Agent] Booting up...")
    agent_client = ArmorIQClient(agent_id="agent-shopping-003")

    # Resolve token file relative to project root (not cwd)
    token_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tokens.json")
    try:
        with open(token_file, "r") as f:
            my_token = json.load(f)["shopping_agent"]
    except Exception as e:
        print(f"[Shopping Agent] Error reading token: {e}")
        return

    try:
        # 1. Valid: search
        res1 = agent_client.invoke(
            token=my_token,
            tool_name="search_items",
            args={"query": "headphones"},
            execute_fn=execute_tool
        )

        # 2. Valid: add to cart
        item_id = res1["results"][0]["id"]
        agent_client.invoke(
            token=my_token,
            tool_name="add_to_cart",
            args={"item_id": item_id, "qty": 1},
            execute_fn=execute_tool
        )

        # 3. SCOPE VIOLATION: attempt checkout (not in scope)
        print("[Shopping Agent] Attempting checkout (should be BLOCKED)...")
        agent_client.invoke(
            token=my_token,
            tool_name="checkout",
            args={"cart_id": "cart-99"},
            execute_fn=execute_tool
        )
    except PermissionError:
        print("[Shopping Agent] Checkout blocked as expected.")
    except Exception as e:
        print(f"[Shopping Agent] Unexpected error: {e}")

    # 4. TTL EXPIRY: wait and retry
    shopping_ttl = int(os.getenv("SHOPPING_AGENT_TTL", "10"))
    # Cap the wait to avoid blocking the demo for too long
    wait_time = min(shopping_ttl + 1, 12)
    print(f"[Shopping Agent] Waiting {wait_time}s to demo token expiry...")
    time.sleep(wait_time)

    try:
        print("[Shopping Agent] Attempting search after expiry (should be EXPIRED)...")
        agent_client.invoke(
            token=my_token,
            tool_name="search_items",
            args={"query": "cable"},
            execute_fn=execute_tool
        )
    except PermissionError:
        print("[Shopping Agent] Token expired as expected.")
    except Exception as e:
        print(f"[Shopping Agent] Unexpected error: {e}")


if __name__ == "__main__":
    main()
