"""
coordinator/main.py
===================
The Coordinator agent. Parses user intent, captures the plan with ArmorIQ,
mints tokens for sub-agents, and spawns them.

Since no API key is used, the parsing logic is mocked to guarantee
a smooth offline hackathon demo.
"""
import sys
import os
import json
import subprocess
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mock_armoriq.client import ArmorIQClient

def main():
    print("=========================================================")
    print("AUTHORCHAIN COORDINATOR")
    print("=========================================================\n")
    
    prompt = "Book me a flight to Delhi, clear my schedule on Thursday, and reorder headphones."
    print(f"USER INTENT: \"{prompt}\"")
    print("\n[Coordinator] Parsing intent into sub-tasks (Mock LLM)...\n")
    
    # Coordinator identity
    client = ArmorIQClient(agent_id="coordinator-root")
    
    # 1. Capture Plan
    # This represents the total allowed intent.
    plan_id = client.capture_plan(
        description=prompt,
        tools=["search_flights", "book_flight", "read_events", "delete_event", "search_items", "add_to_cart"],
        user_email="judge@microsoft.com"
    )
    
    # 2. Delegate to Sub-Agents
    tokens = {}
    
    # Flight Agent gets normal TTL
    tokens["flight_agent"] = client.delegate(
        plan_id=plan_id,
        sub_agent_id="agent-flight-001",
        scope=["search_flights", "book_flight"],
        ttl_seconds=300
    )
    
    # Calendar Agent gets normal TTL
    tokens["calendar_agent"] = client.delegate(
        plan_id=plan_id,
        sub_agent_id="agent-calendar-002",
        scope=["read_events", "delete_event"],
        ttl_seconds=300
    )
    
    # Shopping Agent gets short TTL for expiry demo, and checkout is NOT in scope
    shopping_ttl = int(os.getenv("SHOPPING_AGENT_TTL", "10"))
    tokens["shopping_agent"] = client.delegate(
        plan_id=plan_id,
        sub_agent_id="agent-shopping-003",
        scope=["search_items", "add_to_cart"],
        ttl_seconds=shopping_ttl
    )
    
    # Save tokens for sub-agents to read — use /tmp on Vercel/read-only systems
    if os.environ.get("VERCEL"):
        token_file = "/tmp/tokens.json"
    else:
        token_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tokens.json")
    with open(token_file, "w") as f:
        json.dump(tokens, f)
        
    print("\n[Coordinator] Delegations minted. Spawning sub-agent processes...\n")
    
    # 3. Spawn Sub-Agents (Sequential for clean output in demo)
    agents = [
        "agents/flight_agent.py",
        "agents/calendar_agent.py",
        "agents/shopping_agent.py"
    ]
    
    pythonpath = os.environ.get("PYTHONPATH", ":".join(sys.path))
    env = {**os.environ, "PYTHONUNBUFFERED": "1", "PYTHONPATH": pythonpath}
    for agent_script in agents:
        print(f"\n================ Running {agent_script} ================")
        subprocess.run([sys.executable, agent_script], env=env)
        
    print("\n=========================================================")
    print("Demo Complete. View the Streamlit dashboard for audit logs.")
    print("=========================================================")

if __name__ == "__main__":
    main()
