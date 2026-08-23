"""
custom_coordinator.py
=====================
Custom coordinator that reads GUI configuration and executes user-defined scenarios.
This allows users to control agents through the web interface.
"""
import sys
import os
import json
import subprocess
import time
import httpx
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mock_armoriq.client import ArmorIQClient

def execute_tool(tool_name: str, args: dict, mcp_port: int = 8001) -> dict:
    """Execute a tool against the appropriate MCP server"""
    mcp_url = f"http://localhost:{mcp_port}/tools/call"
    try:
        resp = httpx.post(mcp_url, json={"tool_name": tool_name, "args": args}, timeout=10.0)
        return resp.json()
    except Exception as e:
        return {"error": str(e), "status": "failed"}

def get_mcp_port(tool_name: str) -> int:
    """Map tool names to their MCP server ports"""
    flight_tools = ["search_flights", "book_flight", "cancel_flight"]
    calendar_tools = ["read_events", "create_event", "delete_event", "update_event", "schedule_meeting"]
    shopping_tools = ["search_items", "add_to_cart", "checkout", "track_order"]
    
    if tool_name in flight_tools:
        return 8001
    elif tool_name in calendar_tools:
        return 8002
    elif tool_name in shopping_tools:
        return 8003
    else:
        return 8001  # Default to flight server

def execute_agent_scenario(agent_name: str, config: Dict[str, Any], token: str, client: ArmorIQClient):
    """Execute a specific agent scenario based on GUI configuration"""
    print(f"\n{'='*60}")
    print(f"🤖 Executing {agent_name.upper()} Agent")
    print(f"{'='*60}")
    
    agent_config = config["agents"][agent_name]
    scope = agent_config["scope"]
    args = agent_config["args"]
    
    if not scope:
        print(f"⚠️  [{agent_name.title()} Agent] No permissions granted - skipping")
        return
    
    print(f"🔑 [{agent_name.title()} Agent] Authorized tools: {scope}")
    print(f"⏰ [{agent_name.title()} Agent] TTL: {agent_config['ttl']} seconds")
    
    # Execute authorized operations
    for tool in scope:
        try:
            # Prepare tool arguments based on agent type and GUI inputs
            tool_args = prepare_tool_args(agent_name, tool, args)
            
            print(f"🔧 [{agent_name.title()} Agent] Attempting: {tool}")
            
            # Execute the tool
            result = client.invoke(
                token=token,
                tool_name=tool,
                args=tool_args,
                execute_fn=lambda t, a: execute_tool(t, a, get_mcp_port(t))
            )
            
            print(f"✅ [{agent_name.title()} Agent] {tool} succeeded")
            
        except PermissionError as e:
            print(f"🚫 [{agent_name.title()} Agent] {tool} blocked: {e}")
        except Exception as e:
            print(f"❌ [{agent_name.title()} Agent] {tool} error: {e}")
    
    # Security testing scenarios
    security_config = config["security_tests"]
    
    # Test scope violation
    if security_config.get("scope_violation") and agent_name == "shopping":
        print(f"\n🚨 [{agent_name.title()} Agent] SECURITY TEST: Attempting unauthorized 'checkout'")
        try:
            client.invoke(
                token=token,
                tool_name="checkout",
                args={"cart_id": "test-cart"},
                execute_fn=lambda t, a: execute_tool(t, a, 8003)
            )
            print(f"❌ [{agent_name.title()} Agent] Security test FAILED - unauthorized operation succeeded!")
        except PermissionError as e:
            print(f"✅ [{agent_name.title()} Agent] Security test PASSED - unauthorized operation blocked: {e}")
    
    # Test token expiry
    if security_config.get("token_expiry") and agent_name == "shopping":
        ttl = agent_config["ttl"]
        print(f"\n⏰ [{agent_name.title()} Agent] SECURITY TEST: Waiting {ttl + 2} seconds for token expiry")
        time.sleep(ttl + 2)
        
        try:
            client.invoke(
                token=token,
                tool_name=scope[0] if scope else "search_items",
                args={},
                execute_fn=lambda t, a: execute_tool(t, a, get_mcp_port(t))
            )
            print(f"❌ [{agent_name.title()} Agent] Expiry test FAILED - expired token still works!")
        except PermissionError as e:
            print(f"✅ [{agent_name.title()} Agent] Expiry test PASSED - expired token rejected: {e}")

def prepare_tool_args(agent_name: str, tool_name: str, gui_args: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare tool arguments based on agent type and GUI inputs"""
    
    if agent_name == "flight":
        if tool_name == "search_flights":
            return {
                "origin": gui_args.get("origin", "NYC"),
                "destination": gui_args.get("destination", "TOK")
            }
        elif tool_name == "book_flight":
            return {
                "flight_id": "FL001",  # Mock flight ID
                "passenger_name": gui_args.get("passenger_name", "Demo User")
            }
    
    elif agent_name == "calendar":
        if tool_name == "read_events":
            return {"date": gui_args.get("event_date", "Thursday")}
        elif tool_name == "create_event":
            return {
                "title": gui_args.get("event_title", "Team Meeting"),
                "date": gui_args.get("event_date", "Thursday")
            }
        elif tool_name == "delete_event":
            return {"event_id": "evt_123"}
    
    elif agent_name == "shopping":
        if tool_name == "search_items":
            return {
                "query": gui_args.get("search_query", "wireless headphones"),
                "max_price": gui_args.get("max_price", 200)
            }
        elif tool_name == "add_to_cart":
            return {"item_id": "item_789", "quantity": 1}
        elif tool_name == "checkout":
            return {"cart_id": "cart_456"}
    
    return {}  # Default empty args

def main():
    # Load custom configuration from GUI
    config_path = "custom_config.json"
    if not os.path.exists(config_path):
        print("❌ No custom configuration found. Use the GUI to create a scenario.")
        return
    
    with open(config_path, "r") as f:
        config = json.load(f)
    
    print("🎮" + "="*60)
    print("🎮 ARGUS CUSTOM AGENT CONTROL SYSTEM")
    print("🎮" + "="*60)
    print(f"👤 USER INTENT: \"{config['user_intent']}\"")
    print(f"👤 USER EMAIL: {config['user_email']}")
    print(f"🛠️  AVAILABLE TOOLS: {', '.join(config['available_tools'])}")
    print("🎮" + "="*60)
    
    # Initialize coordinator
    client = ArmorIQClient(agent_id="coordinator-gui")
    
    # Capture plan with custom configuration
    plan_id = client.capture_plan(
        description=config["user_intent"],
        tools=config["available_tools"],
        user_email=config["user_email"]
    )
    
    # Create delegation tokens for each configured agent
    tokens = {}
    
    for agent_name, agent_config in config["agents"].items():
        if agent_config["scope"]:  # Only create tokens for agents with permissions
            agent_id = f"agent-{agent_name}-gui"
            
            tokens[agent_name] = client.delegate(
                plan_id=plan_id,
                sub_agent_id=agent_id,
                scope=agent_config["scope"],
                ttl_seconds=agent_config["ttl"]
            )
            
            print(f"🔑 Created token for {agent_name} agent: {agent_config['scope']} (TTL: {agent_config['ttl']}s)")
    
    print(f"\n🚀 Executing {len(tokens)} configured agents...\n")
    
    # Execute each agent scenario
    for agent_name, token in tokens.items():
        agent_client = ArmorIQClient(agent_id=f"agent-{agent_name}-gui")
        execute_agent_scenario(agent_name, config, token, agent_client)
        
        # Small delay between agents for clearer output
        time.sleep(1)
    
    print("\n🎮" + "="*60)
    print("✅ CUSTOM SCENARIO EXECUTION COMPLETE!")
    print("🎮" + "="*60)
    print("📊 Check the 'Real-Time Audit Trail' tab in the GUI to see all operations")
    print("🎮" + "="*60)

if __name__ == "__main__":
    main()