"""
tests/test_argus.py
=========================
Comprehensive test suite for Argus governance, ArmorIQ SDK client,
scope enforcement, TTL expiry, HMAC signature verification, and audit logging.
"""

import os
import sys
import time
import json
import sqlite3
import pytest

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


def dummy_execute_tool(tool_name: str, args: dict) -> dict:
    """Dummy tool executor function."""
    return {"status": "success", "tool": tool_name, "args": args}


class TestArmorIQGovernance:

    def test_client_initialization(self):
        """Test ArmorIQClient initialization for coordinator and sub-agents."""
        client = ArmorIQClient(agent_id="test-coordinator")
        assert client.agent_id == "test-coordinator"
        assert client._secret is not None

    def test_capture_plan(self, temp_db):
        """Test intent plan capture, canonicalization, and database logging."""
        _, logger = temp_db
        client = ArmorIQClient(agent_id="test-coordinator")
        
        tools = ["search_flights", "book_flight", "read_events"]
        plan_id = client.capture_plan(
            description="Book flight to Delhi and read schedule",
            tools=tools,
            user_email="testuser@example.com"
        )
        
        assert plan_id is not None
        assert plan_id.startswith("plan-")
        
        # Verify SQLite DB record
        conn = sqlite3.connect(logger.db_path)
        row = conn.execute("SELECT plan_id, description, declared_tools, user_email FROM plans WHERE plan_id = ?", (plan_id,)).fetchone()
        assert row is not None
        assert row[0] == plan_id
        assert row[1] == "Book flight to Delhi and read schedule"
        assert json.loads(row[2]) == tools
        assert row[3] == "testuser@example.com"
        conn.close()

    def test_delegate_minting(self, temp_db):
        """Test delegate token generation and HMAC-SHA256 signature."""
        _, logger = temp_db
        client = ArmorIQClient(agent_id="test-coordinator")
        
        plan_id = "plan-test-123"
        scope = ["search_flights", "book_flight"]
        token = client.delegate(
            plan_id=plan_id,
            sub_agent_id="agent-flight-001",
            scope=scope,
            ttl_seconds=300
        )
        
        assert token is not None
        assert "." in token
        
        payload, status = client._verify_token(token)
        assert status == "VALID"
        assert payload["plan_id"] == plan_id
        assert payload["agent_id"] == "agent-flight-001"
        assert payload["scope"] == scope
        assert payload["issued_by"] == "test-coordinator"

    def test_invoke_authorized(self, temp_db):
        """Test invoking a tool that is within the delegated scope and valid TTL."""
        _, logger = temp_db
        coordinator = ArmorIQClient(agent_id="test-coordinator")
        sub_agent = ArmorIQClient(agent_id="agent-flight-001")
        
        plan_id = coordinator.capture_plan("Test plan", ["search_flights", "book_flight"])
        token = coordinator.delegate(
            plan_id=plan_id,
            sub_agent_id="agent-flight-001",
            scope=["search_flights", "book_flight"],
            ttl_seconds=300
        )
        
        result = sub_agent.invoke(
            token=token,
            tool_name="search_flights",
            args={"origin": "BOM", "destination": "DEL"},
            execute_fn=dummy_execute_tool
        )
        
        assert result["status"] == "success"
        assert result["tool"] == "search_flights"
        
        # Verify ALLOWED status in audit DB
        conn = sqlite3.connect(logger.db_path)
        row = conn.execute("SELECT tool_name, status FROM invocations WHERE agent_id = ?", ("agent-flight-001",)).fetchone()
        assert row is not None
        assert row[0] == "search_flights"
        assert row[1] == "ALLOWED"
        conn.close()

    def test_invoke_scope_violation(self, temp_db):
        """Test invoking a tool NOT in the delegated scope raises SCOPE VIOLATION."""
        _, logger = temp_db
        coordinator = ArmorIQClient(agent_id="test-coordinator")
        sub_agent = ArmorIQClient(agent_id="agent-shopping-003")
        
        plan_id = coordinator.capture_plan("Shopping plan", ["search_items", "add_to_cart"])
        token = coordinator.delegate(
            plan_id=plan_id,
            sub_agent_id="agent-shopping-003",
            scope=["search_items", "add_to_cart"], # checkout is missing!
            ttl_seconds=300
        )
        
        with pytest.raises(PermissionError) as exc_info:
            sub_agent.invoke(
                token=token,
                tool_name="checkout", # Unauthorized action!
                args={"cart_id": "c1"},
                execute_fn=dummy_execute_tool
            )
            
        assert "SCOPE VIOLATION" in str(exc_info.value)
        
        # Verify BLOCKED status in audit DB
        conn = sqlite3.connect(logger.db_path)
        row = conn.execute("SELECT tool_name, status FROM invocations WHERE agent_id = ?", ("agent-shopping-003",)).fetchone()
        assert row is not None
        assert row[0] == "checkout"
        assert row[1] == "BLOCKED"
        conn.close()

    def test_invoke_token_expired(self, temp_db):
        """Test invoking a tool after token TTL expiry raises EXPIRED."""
        _, logger = temp_db
        coordinator = ArmorIQClient(agent_id="test-coordinator")
        sub_agent = ArmorIQClient(agent_id="agent-shopping-003")
        
        plan_id = coordinator.capture_plan("Short TTL plan", ["search_items"])
        token = coordinator.delegate(
            plan_id=plan_id,
            sub_agent_id="agent-shopping-003",
            scope=["search_items"],
            ttl_seconds=1 # 1 second TTL
        )
        
        time.sleep(1.2) # Wait for expiry
        
        with pytest.raises(PermissionError) as exc_info:
            sub_agent.invoke(
                token=token,
                tool_name="search_items",
                args={"query": "cable"},
                execute_fn=dummy_execute_tool
            )
            
        assert "EXPIRED" in str(exc_info.value)
        
        # Verify EXPIRED status in audit DB
        conn = sqlite3.connect(logger.db_path)
        row = conn.execute("SELECT tool_name, status FROM invocations WHERE agent_id = ?", ("agent-shopping-003",)).fetchone()
        assert row is not None
        assert row[0] == "search_items"
        assert row[1] == "EXPIRED"
        conn.close()

    def test_invoke_tampered_token_signature(self, temp_db):
        """Test invoking a tool with a tampered token raises INVALID SIGNATURE."""
        _, logger = temp_db
        coordinator = ArmorIQClient(agent_id="test-coordinator")
        sub_agent = ArmorIQClient(agent_id="agent-hacker")
        
        plan_id = coordinator.capture_plan("Plan", ["search_flights"])
        valid_token = coordinator.delegate(plan_id=plan_id, sub_agent_id="agent-hacker", scope=["search_flights"], ttl_seconds=300)
        
        # Tamper token signature
        payload_part, _ = valid_token.rsplit(".", 1)
        tampered_token = f"{payload_part}.invalid_fake_signature"
        
        with pytest.raises(PermissionError) as exc_info:
            sub_agent.invoke(
                token=tampered_token,
                tool_name="search_flights",
                args={},
                execute_fn=dummy_execute_tool
            )
            
        assert "verification failed" in str(exc_info.value)
