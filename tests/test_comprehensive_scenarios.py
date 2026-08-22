"""
tests/test_comprehensive_scenarios.py
====================================
Enhanced comprehensive test suite for Argus with various scenarios,
edge cases, and real-world use cases for the hackathon demonstration.
"""

import os
import sys
import time
import json
import sqlite3
import pytest
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Ensure project root is in import path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from mock_armoriq.client import ArmorIQClient
from audit.logger import AuditLogger


@pytest.fixture
def temp_db(tmp_path):
    """Fixture to provide a clean isolated SQLite database for testing."""
    db_file = str(tmp_path / "test_audit.db")
    os.environ["ARGUS_DB"] = db_file
    logger = AuditLogger(db_path=db_file)
    yield db_file, logger
    # Cleanup env
    if "ARGUS_DB" in os.environ:
        del os.environ["ARGUS_DB"]


def mock_tool_executor(tool_name: str, args: dict) -> dict:
    """Enhanced mock tool executor that simulates real tool responses."""
    responses = {
        "search_flights": {
            "status": "success",
            "flights": [
                {"id": "FL001", "origin": "BOM", "destination": "DEL", "price": 5500},
                {"id": "FL002", "origin": "BOM", "destination": "DEL", "price": 6200}
            ]
        },
        "book_flight": {
            "status": "success",
            "booking_id": "BK12345",
            "confirmation": "Flight booked successfully"
        },
        "read_events": {
            "status": "success",
            "events": [
                {"id": "E001", "title": "Meeting", "date": "2026-08-28", "time": "14:00"},
                {"id": "E002", "title": "Workshop", "date": "2026-08-29", "time": "10:00"}
            ]
        },
        "delete_event": {
            "status": "success",
            "deleted_event_id": args.get("event_id", "E001"),
            "message": "Event deleted successfully"
        },
        "search_items": {
            "status": "success",
            "results": [
                {"id": "I001", "name": "Wireless Headphones", "price": 2500},
                {"id": "I002", "name": "USB Cable", "price": 500}
            ]
        },
        "add_to_cart": {
            "status": "success",
            "cart_id": "cart-99",
            "item_added": args.get("item_id", "I001")
        },
        "checkout": {
            "status": "success",
            "order_id": "ORD-987654",
            "total": 3000
        }
    }
    
    return responses.get(tool_name, {"status": "error", "message": f"Unknown tool: {tool_name}"})


class TestComprehensiveScenarios:
    """Comprehensive test scenarios for Argus governance system."""

    def test_full_workflow_happy_path(self, temp_db):
        """Test complete workflow from plan capture to successful tool execution."""
        _, logger = temp_db
        
        # Initialize coordinator
        coordinator = ArmorIQClient(agent_id="coordinator-main")
        
        # Capture comprehensive plan
        plan_id = coordinator.capture_plan(
            description="Complete travel booking and shopping workflow",
            tools=["search_flights", "book_flight", "read_events", "delete_event", "search_items", "add_to_cart"],
            user_email="user@example.com"
        )
        
        assert plan_id.startswith("plan-")
        
        # Delegate to flight agent
        flight_token = coordinator.delegate(
            plan_id=plan_id,
            sub_agent_id="agent-flight-001",
            scope=["search_flights", "book_flight"],
            ttl_seconds=600
        )
        
        # Delegate to calendar agent  
        calendar_token = coordinator.delegate(
            plan_id=plan_id,
            sub_agent_id="agent-calendar-002",
            scope=["read_events", "delete_event"],
            ttl_seconds=600
        )
        
        # Initialize sub-agents
        flight_agent = ArmorIQClient(agent_id="agent-flight-001")
        calendar_agent = ArmorIQClient(agent_id="agent-calendar-002")
        
        # Execute flight operations
        search_result = flight_agent.invoke(
            token=flight_token,
            tool_name="search_flights",
            args={"origin": "BOM", "destination": "DEL"},
            execute_fn=mock_tool_executor
        )
        
        assert search_result["status"] == "success"
        assert len(search_result["flights"]) > 0
        
        book_result = flight_agent.invoke(
            token=flight_token,
            tool_name="book_flight",
            args={"flight_id": "FL001"},
            execute_fn=mock_tool_executor
        )
        
        assert book_result["status"] == "success"
        assert "booking_id" in book_result
        
        # Execute calendar operations
        events_result = calendar_agent.invoke(
            token=calendar_token,
            tool_name="read_events",
            args={},
            execute_fn=mock_tool_executor
        )
        
        assert events_result["status"] == "success"
        assert len(events_result["events"]) > 0
        
        # Verify audit logs
        conn = sqlite3.connect(logger.db_path)
        
        # Check plan creation
        plan_row = conn.execute(
            "SELECT description, declared_tools FROM plans WHERE plan_id = ?", 
            (plan_id,)
        ).fetchone()
        assert plan_row is not None
        assert "Complete travel booking" in plan_row[0]
        
        # Check successful invocations
        invocations = conn.execute(
            "SELECT agent_id, tool_name, status FROM invocations WHERE plan_id = ? ORDER BY timestamp",
            (plan_id,)
        ).fetchall()
        
        assert len(invocations) >= 3
        
        # Verify all are ALLOWED
        statuses = [inv[2] for inv in invocations]
        assert all(status == "ALLOWED" for status in statuses)
        
        conn.close()

    def test_multi_agent_concurrent_operations(self, temp_db):
        """Test multiple agents operating concurrently with different scopes."""
        _, logger = temp_db
        
        coordinator = ArmorIQClient(agent_id="coordinator-concurrent")
        
        plan_id = coordinator.capture_plan(
            description="Concurrent multi-agent operations",
            tools=["search_flights", "read_events", "search_items"],
            user_email="concurrent@example.com"
        )
        
        # Create tokens for different agents with overlapping capabilities
        flight_token = coordinator.delegate(
            plan_id=plan_id,
            sub_agent_id="agent-flight-multi",
            scope=["search_flights"],
            ttl_seconds=300
        )
        
        calendar_token = coordinator.delegate(
            plan_id=plan_id,
            sub_agent_id="agent-calendar-multi",
            scope=["read_events"],
            ttl_seconds=300
        )
        
        shopping_token = coordinator.delegate(
            plan_id=plan_id,
            sub_agent_id="agent-shopping-multi",
            scope=["search_items"],
            ttl_seconds=300
        )
        
        # Initialize agents
        agents = {
            "flight": ArmorIQClient(agent_id="agent-flight-multi"),
            "calendar": ArmorIQClient(agent_id="agent-calendar-multi"),
            "shopping": ArmorIQClient(agent_id="agent-shopping-multi")
        }
        
        tokens = {
            "flight": flight_token,
            "calendar": calendar_token,
            "shopping": shopping_token
        }
        
        tools = {
            "flight": "search_flights",
            "calendar": "read_events", 
            "shopping": "search_items"
        }
        
        # Execute operations for all agents
        results = {}
        for agent_type in ["flight", "calendar", "shopping"]:
            results[agent_type] = agents[agent_type].invoke(
                token=tokens[agent_type],
                tool_name=tools[agent_type],
                args={},
                execute_fn=mock_tool_executor
            )
        
        # Verify all operations succeeded
        for agent_type, result in results.items():
            assert result["status"] == "success"
            
        # Verify audit trail shows all operations
        conn = sqlite3.connect(logger.db_path)
        invocations = conn.execute(
            "SELECT agent_id, tool_name, status FROM invocations WHERE plan_id = ?",
            (plan_id,)
        ).fetchall()
        
        assert len(invocations) == 3
        agent_ids = [inv[0] for inv in invocations]
        assert "agent-flight-multi" in agent_ids
        assert "agent-calendar-multi" in agent_ids
        assert "agent-shopping-multi" in agent_ids
        
        conn.close()

    def test_escalating_security_violations(self, temp_db):
        """Test multiple types of security violations from the same agent."""
        _, logger = temp_db
        
        coordinator = ArmorIQClient(agent_id="coordinator-security")
        malicious_agent = ArmorIQClient(agent_id="agent-malicious")
        
        plan_id = coordinator.capture_plan(
            description="Limited scope plan for security testing",
            tools=["search_items"],
            user_email="security@example.com"
        )
        
        # Create very limited token
        token = coordinator.delegate(
            plan_id=plan_id,
            sub_agent_id="agent-malicious",
            scope=["search_items"],  # Only search allowed
            ttl_seconds=5  # Short TTL for expiry test
        )
        
        # Test 1: Valid operation
        result = malicious_agent.invoke(
            token=token,
            tool_name="search_items",
            args={"query": "test"},
            execute_fn=mock_tool_executor
        )
        assert result["status"] == "success"
        
        # Test 2: Scope violation - unauthorized tool
        with pytest.raises(PermissionError) as exc_info:
            malicious_agent.invoke(
                token=token,
                tool_name="checkout",  # Not in scope!
                args={"cart_id": "malicious"},
                execute_fn=mock_tool_executor
            )
        assert "SCOPE VIOLATION" in str(exc_info.value)
        
        # Test 3: Another scope violation - different unauthorized tool
        with pytest.raises(PermissionError) as exc_info:
            malicious_agent.invoke(
                token=token,
                tool_name="book_flight",  # Not in scope!
                args={"flight_id": "malicious"},
                execute_fn=mock_tool_executor
            )
        assert "SCOPE VIOLATION" in str(exc_info.value)
        
        # Test 4: Wait for token expiry
        time.sleep(6)
        
        with pytest.raises(PermissionError) as exc_info:
            malicious_agent.invoke(
                token=token,
                tool_name="search_items",  # In scope but expired
                args={"query": "expired"},
                execute_fn=mock_tool_executor
            )
        assert "EXPIRED" in str(exc_info.value)
        
        # Verify security audit trail
        conn = sqlite3.connect(logger.db_path)
        invocations = conn.execute(
            "SELECT tool_name, status, reason FROM invocations WHERE agent_id = ? ORDER BY timestamp",
            ("agent-malicious",)
        ).fetchall()
        
        # Should have: 1 ALLOWED, 2 BLOCKED (scope violations), 1 EXPIRED
        assert len(invocations) == 4
        
        statuses = [inv[1] for inv in invocations]
        assert statuses[0] == "ALLOWED"
        assert statuses[1] == "BLOCKED"
        assert statuses[2] == "BLOCKED"
        assert statuses[3] == "EXPIRED"
        
        # Check rejection reasons
        assert "SCOPE VIOLATION" in invocations[1][2]
        assert "SCOPE VIOLATION" in invocations[2][2]
        assert "expired" in invocations[3][2] or "EXPIRED" in invocations[3][2]
        
        conn.close()

    def test_token_signature_manipulation_attempts(self, temp_db):
        """Test various token tampering and signature manipulation attempts."""
        _, logger = temp_db
        
        coordinator = ArmorIQClient(agent_id="coordinator-tamper")
        attacker_agent = ArmorIQClient(agent_id="agent-attacker")
        
        plan_id = coordinator.capture_plan(
            description="Token tampering test plan",
            tools=["search_items", "add_to_cart"],
            user_email="tamper@example.com"
        )
        
        # Create legitimate token
        legitimate_token = coordinator.delegate(
            plan_id=plan_id,
            sub_agent_id="agent-attacker",
            scope=["search_items"],
            ttl_seconds=300
        )
        
        # Test 1: Completely fake token
        fake_token = "fake.payload.signature"
        with pytest.raises(PermissionError):
            attacker_agent.invoke(
                token=fake_token,
                tool_name="search_items",
                args={},
                execute_fn=mock_tool_executor
            )
        
        # Test 2: Modified payload with original signature
        payload, signature = legitimate_token.rsplit(".", 1)
        
        # Decode and modify the payload to expand scope
        import base64
        import json
        decoded_payload = json.loads(base64.b64decode(payload + "=="))
        decoded_payload["scope"].append("checkout")  # Try to add unauthorized scope
        
        modified_payload = base64.b64encode(json.dumps(decoded_payload).encode()).decode().rstrip("=")
        tampered_token = f"{modified_payload}.{signature}"
        
        with pytest.raises(PermissionError):
            attacker_agent.invoke(
                token=tampered_token,
                tool_name="checkout",
                args={},
                execute_fn=mock_tool_executor
            )
        
        # Test 3: Original payload with fake signature
        fake_signature_token = f"{payload}.fakesignaturehash"
        with pytest.raises(PermissionError):
            attacker_agent.invoke(
                token=fake_signature_token,
                tool_name="search_items",
                args={},
                execute_fn=mock_tool_executor
            )

    def test_cross_plan_token_reuse_attempt(self, temp_db):
        """Test attempt to reuse tokens across different plans."""
        _, logger = temp_db
        
        coordinator = ArmorIQClient(agent_id="coordinator-cross-plan")
        agent = ArmorIQClient(agent_id="agent-cross-plan")
        
        # Create first plan
        plan1_id = coordinator.capture_plan(
            description="First plan for flights",
            tools=["search_flights", "book_flight"],
            user_email="cross1@example.com"
        )
        
        token1 = coordinator.delegate(
            plan_id=plan1_id,
            sub_agent_id="agent-cross-plan",
            scope=["search_flights"],
            ttl_seconds=300
        )
        
        # Create second plan
        plan2_id = coordinator.capture_plan(
            description="Second plan for shopping",
            tools=["search_items", "add_to_cart"],
            user_email="cross2@example.com"
        )
        
        token2 = coordinator.delegate(
            plan_id=plan2_id,
            sub_agent_id="agent-cross-plan",
            scope=["search_items"],
            ttl_seconds=300
        )
        
        # Valid usage: Use token1 for flight operations
        result1 = agent.invoke(
            token=token1,
            tool_name="search_flights",
            args={},
            execute_fn=mock_tool_executor
        )
        assert result1["status"] == "success"
        
        # Valid usage: Use token2 for shopping operations
        result2 = agent.invoke(
            token=token2,
            tool_name="search_items",
            args={},
            execute_fn=mock_tool_executor
        )
        assert result2["status"] == "success"
        
        # Invalid usage: Try to use flight token for shopping
        with pytest.raises(PermissionError) as exc_info:
            agent.invoke(
                token=token1,  # Flight token
                tool_name="search_items",  # Shopping tool
                args={},
                execute_fn=mock_tool_executor
            )
        assert "SCOPE VIOLATION" in str(exc_info.value)

    def test_performance_stress_scenario(self, temp_db):
        """Test system performance under stress with many operations."""
        _, logger = temp_db
        
        coordinator = ArmorIQClient(agent_id="coordinator-stress")
        
        # Create plan with many tools
        all_tools = [
            "search_flights", "book_flight", 
            "read_events", "delete_event",
            "search_items", "add_to_cart"
        ]
        
        plan_id = coordinator.capture_plan(
            description="Stress test with many operations",
            tools=all_tools,
            user_email="stress@example.com"
        )
        
        # Create multiple agents
        num_agents = 5
        agents = []
        tokens = []
        
        for i in range(num_agents):
            agent_id = f"agent-stress-{i:03d}"
            agents.append(ArmorIQClient(agent_id=agent_id))
            
            token = coordinator.delegate(
                plan_id=plan_id,
                sub_agent_id=agent_id,
                scope=all_tools,
                ttl_seconds=600
            )
            tokens.append(token)
        
        # Execute many operations
        num_operations = 50
        successful_operations = 0
        
        start_time = time.time()
        
        for i in range(num_operations):
            agent_idx = i % num_agents
            tool_idx = i % len(all_tools)
            
            try:
                result = agents[agent_idx].invoke(
                    token=tokens[agent_idx],
                    tool_name=all_tools[tool_idx],
                    args={"operation_id": i},
                    execute_fn=mock_tool_executor
                )
                if result["status"] == "success":
                    successful_operations += 1
            except Exception as e:
                print(f"Operation {i} failed: {e}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Verify performance metrics
        assert successful_operations >= num_operations * 0.95  # 95% success rate
        assert duration < 30  # Should complete within 30 seconds
        
        operations_per_second = successful_operations / duration
        assert operations_per_second > 1  # At least 1 operation per second
        
        print(f"Stress Test Results:")
        print(f"  Operations: {successful_operations}/{num_operations}")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Rate: {operations_per_second:.2f} ops/sec")


class TestOutputFormatValidation:
    """Tests for validating output formats and data structures."""

    def test_plan_output_format(self, temp_db):
        """Test the format of plan capture output."""
        _, logger = temp_db
        
        coordinator = ArmorIQClient(agent_id="coordinator-format")
        
        plan_id = coordinator.capture_plan(
            description="Format validation test",
            tools=["search_flights", "book_flight"],
            user_email="format@example.com"
        )
        
        # Verify plan ID format
        assert isinstance(plan_id, str)
        assert plan_id.startswith("plan-")
        assert len(plan_id) > 10  # Should have reasonable length
        
        # Verify database storage format
        conn = sqlite3.connect(logger.db_path)
        row = conn.execute(
            "SELECT plan_id, description, declared_tools, user_email, timestamp FROM plans WHERE plan_id = ?",
            (plan_id,)
        ).fetchone()
        
        assert row is not None
        assert row[0] == plan_id
        assert row[1] == "Format validation test"
        
        # Verify tools are stored as valid JSON array
        declared_tools = json.loads(row[2])
        assert isinstance(declared_tools, list)
        assert "search_flights" in declared_tools
        assert "book_flight" in declared_tools
        
        assert row[3] == "format@example.com"
        
        # Verify timestamp format (should be ISO format)
        timestamp = row[4]
        assert isinstance(timestamp, str)
        assert "T" in timestamp  # ISO format includes T
        
        conn.close()

    def test_delegation_output_format(self, temp_db):
        """Test the format of delegation token output."""
        _, logger = temp_db
        
        coordinator = ArmorIQClient(agent_id="coordinator-delegation")
        
        plan_id = coordinator.capture_plan(
            description="Delegation format test",
            tools=["search_flights"],
            user_email="delegation@example.com"
        )
        
        token = coordinator.delegate(
            plan_id=plan_id,
            sub_agent_id="agent-delegation-test",
            scope=["search_flights"],
            ttl_seconds=300
        )
        
        # Verify token format (should be base64.signature)
        assert isinstance(token, str)
        assert "." in token
        
        parts = token.split(".")
        assert len(parts) == 2
        
        payload_part, signature_part = parts
        
        # Verify payload is valid base64 and contains expected fields
        import base64
        import json
        
        try:
            decoded = base64.b64decode(payload_part + "==")
            payload_data = json.loads(decoded)
            
            required_fields = ["plan_id", "agent_id", "scope", "exp", "iat", "issued_by", "delegation_id"]
            for field in required_fields:
                assert field in payload_data, f"Missing required field: {field}"
            
            assert payload_data["plan_id"] == plan_id
            assert payload_data["agent_id"] == "agent-delegation-test"
            assert payload_data["scope"] == ["search_flights"]
            assert payload_data["issued_by"] == "coordinator-delegation"
            
            # Verify timestamps are numbers (Unix timestamps as floats)
            assert isinstance(payload_data["iat"], (int, float))
            assert isinstance(payload_data["exp"], (int, float))
            assert payload_data["exp"] > payload_data["iat"]
            
        except Exception as e:
            pytest.fail(f"Token payload format validation failed: {e}")
        
        # Verify signature is not empty
        assert len(signature_part) > 0

    def test_invocation_audit_output_format(self, temp_db):
        """Test the format of invocation audit log output."""
        _, logger = temp_db
        
        coordinator = ArmorIQClient(agent_id="coordinator-audit")
        agent = ArmorIQClient(agent_id="agent-audit-test")
        
        plan_id = coordinator.capture_plan(
            description="Audit format test",
            tools=["search_flights"],
            user_email="audit@example.com"
        )
        
        token = coordinator.delegate(
            plan_id=plan_id,
            sub_agent_id="agent-audit-test",
            scope=["search_flights"],
            ttl_seconds=300
        )
        
        # Execute operation
        result = agent.invoke(
            token=token,
            tool_name="search_flights",
            args={"origin": "BOM", "destination": "DEL"},
            execute_fn=mock_tool_executor
        )
        
        # Verify invocation audit log format
        conn = sqlite3.connect(logger.db_path)
        row = conn.execute(
            """SELECT plan_id, agent_id, tool_name, args, status, 
                      reason, timestamp 
               FROM invocations WHERE agent_id = ?""",
            ("agent-audit-test",)
        ).fetchone()
        
        assert row is not None
        
        # Verify all required fields are present
        plan_id_db, agent_id, tool_name, tool_args, status, reason, timestamp = row
        
        assert plan_id_db == plan_id
        assert agent_id == "agent-audit-test"
        assert tool_name == "search_flights"
        
        # Verify tool_args is valid JSON
        args_data = json.loads(tool_args)
        assert args_data["origin"] == "BOM"
        assert args_data["destination"] == "DEL"
        
        assert status == "ALLOWED"
        # For successful operations, reason contains success message
        assert reason is not None
        
        # Verify timestamp format
        assert isinstance(timestamp, str)
        assert "T" in timestamp
        
        conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])