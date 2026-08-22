# Argus Test Cases & Output Documentation

## Overview

This document outlines the test cases for Argus, a multi-agent system with cryptographic intent verification.

## Test Execution

### Quick Start
```bash
# Run all tests with detailed output
python3 run_tests.py

# Run individual test suites
python3 -m pytest tests/test_authorchain.py -v
python3 -m pytest tests/test_comprehensive_scenarios.py -v

# Run the full demo
./run_demo.sh
```

## Test Categories

### 1. Core Unit Tests (`test_authorchain.py`)

| Test Case | Purpose | Expected Output |
|-----------|---------|-----------------|
| `test_client_initialization` | Verify ArmorIQ client setup | Client object with agent_id and secret |
| `test_capture_plan` | Test plan creation and DB storage | Plan ID starting with `plan-` |
| `test_delegate_minting` | Test token generation with HMAC | Valid JWT-like token with signature |
| `test_invoke_authorized` | Test successful tool execution | Status: `ALLOWED` in audit log |
| `test_invoke_scope_violation` | Test unauthorized tool blocking | PermissionError with `SCOPE VIOLATION` |
| `test_invoke_token_expired` | Test TTL enforcement | PermissionError with `EXPIRED` |
| `test_invoke_tampered_token_signature` | Test signature verification | PermissionError with `verification failed` |

### 2. Comprehensive Scenario Tests (`test_comprehensive_scenarios.py`)

#### 2.1 Full Workflow Tests
- test_full_workflow_happy_path: Complete end-to-end workflow
  - Creates plan, delegates to multiple agents
  - Executes flight booking, calendar management
  - Verifies all operations are ALLOWED in audit logs

#### 2.2 Security & Edge Cases
- test_multi_agent_concurrent_operations: Concurrent multi-agent execution
- test_escalating_security_violations: Multiple violation types from same agent
- test_token_signature_manipulation_attempts: Various token tampering scenarios
- test_cross_plan_token_reuse_attempt: Cross-plan token abuse prevention

#### 2.3 Performance Tests
- test_performance_stress_scenario: High-load testing with 50+ operations

#### 2.4 Output Format Validation
- test_plan_output_format: Plan ID and database format validation
- test_delegation_output_format: Token structure and payload verification
- test_invocation_audit_output_format: Audit log format compliance

## Expected Output Formats

### 1. Plan Capture Output

#### Console Output
```
[ArmorIQ] ┌── capture_plan ──────────────────────────────────────
[ArmorIQ] │  plan_id : plan-c144145f82
[ArmorIQ] │  intent  : Book me a flight to Delhi, clear my schedule on Thursday, and reorder headphones
[ArmorIQ] │  tools   : ['search_flights', 'book_flight', 'read_events', 'delete_event', 'search_items', 'add_to_cart']
[ArmorIQ] │  user    : judge@microsoft.com
[ArmorIQ] └─────────────────────────────────────────────────────
```

#### Database Schema
```sql
CREATE TABLE plans (
    plan_id TEXT PRIMARY KEY,           -- Format: "plan-" + 10-char hash
    description TEXT NOT NULL,          -- User intent description
    declared_tools TEXT NOT NULL,       -- JSON array of tool names
    user_email TEXT NOT NULL,           -- User identifier
    timestamp TEXT NOT NULL             -- ISO 8601 format
);
```

#### Sample Database Record
```json
{
    "plan_id": "plan-c144145f82",
    "description": "Book me a flight to Delhi, clear my schedule on Thursday, and reorder headphones",
    "declared_tools": "[\"search_flights\", \"book_flight\", \"read_events\", \"delete_event\", \"search_items\", \"add_to_cart\"]",
    "user_email": "judge@microsoft.com",
    "timestamp": "2026-08-23T15:41:41.123456"
}
```

### 2. Token Delegation Output

#### Console Output
```
[ArmorIQ] delegate() → agent-flight-001
           scope     : ['search_flights', 'book_flight']
           ttl       : 300s  expires: 03:46:41
           del_id    : del-bb608bb574
```

#### Token Structure
```
Format: <base64_payload>.<hmac_signature>
Example: eyJwbGFuX2lkIjoicGxhbi1jMTQ0MTQ1ZjgyIiwiYWdlbnRfaWQiOiJhZ2VudC1mbGlnaHQtMDAxIiwic2NvcGUiOlsic2VhcmNoX2ZsaWdodHMiLCJib29rX2ZsaWdodCJdLCJleHAiOjE2OTMyOTQ2MDEsImlhdCI6MTY5MzI5NDMwMSwiaXNzdWVkX2J5IjoiY29vcmRpbmF0b3Itcm9vdCJ9.a8f5f167f44f4964e6c998dee827110c
```

#### Decoded Payload
```json
{
    "plan_id": "plan-c144145f82",
    "agent_id": "agent-flight-001",
    "scope": ["search_flights", "book_flight"],
    "exp": 1693294601,
    "iat": 1693294301,
    "issued_by": "coordinator-root"
}
```

### 3. Invocation Results

#### Successful Invocation
```
[ArmorIQ] invoke() ▶  tool=search_flights  agent=agent-flight-001
[ArmorIQ]   ✓ AUTHORIZED  scope=['search_flights', 'book_flight']  ttl_remaining=300s
```

#### Scope Violation
```
[ArmorIQ] invoke() ▶  tool=checkout  agent=agent-shopping-003
[ArmorIQ]   ✗ SCOPE VIOLATION
[ArmorIQ]      tool          : checkout
[ArmorIQ]      allowed scope : ['search_items', 'add_to_cart']
[ArmorIQ]      delegated_by  : coordinator-root
[ArmorIQ]      plan_id       : plan-c144145f82
```

#### Token Expiry
```
[ArmorIQ] invoke() ▶  tool=search_items  agent=agent-shopping-003
[ArmorIQ]   ⚠  TOKEN EXPIRED  Delegation token expired 1.6s ago — re-delegation required
[ArmorIQ]      delegated_by=coordinator-root  plan=plan-c144145f82
```

### 4. Audit Database Schema

```sql
CREATE TABLE invocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id TEXT NOT NULL,              -- Links to plans table
    agent_id TEXT NOT NULL,             -- Sub-agent identifier
    tool_name TEXT NOT NULL,            -- Tool being invoked
    tool_args TEXT NOT NULL,            -- JSON-encoded arguments
    status TEXT NOT NULL,               -- 'ALLOWED', 'BLOCKED', 'EXPIRED'
    rejection_reason TEXT,              -- NULL for ALLOWED, reason for others
    timestamp TEXT NOT NULL,            -- ISO 8601 format
    token_hash TEXT NOT NULL,           -- SHA-256 hash of token
    FOREIGN KEY (plan_id) REFERENCES plans (plan_id)
);
```

#### Sample Audit Records
```json
[
    {
        "plan_id": "plan-c144145f82",
        "agent_id": "agent-flight-001",
        "tool_name": "search_flights",
        "tool_args": "{\"origin\": \"BOM\", \"destination\": \"DEL\"}",
        "status": "ALLOWED",
        "rejection_reason": null,
        "timestamp": "2026-08-23T15:41:45.678901",
        "token_hash": "sha256:a8f5f167f44f4964e6c998dee827110c..."
    },
    {
        "plan_id": "plan-c144145f82", 
        "agent_id": "agent-shopping-003",
        "tool_name": "checkout",
        "tool_args": "{\"cart_id\": \"cart-99\"}",
        "status": "BLOCKED",
        "rejection_reason": "SCOPE VIOLATION: Tool 'checkout' not in allowed scope ['search_items', 'add_to_cart']",
        "timestamp": "2026-08-23T15:41:48.123456",
        "token_hash": "sha256:b9e6e278f55e5075f7d999eff938221d..."
    }
]
```

## Error Output Formats

### 1. Permission Errors

#### Scope Violation
```python
PermissionError: SCOPE VIOLATION: Tool 'checkout' not in allowed scope ['search_items', 'add_to_cart']. Plan: plan-c144145f82, Delegated by: coordinator-root
```

#### Token Expiry
```python
PermissionError: TOKEN EXPIRED: Delegation token expired 1.6s ago — re-delegation required. Plan: plan-c144145f82, Delegated by: coordinator-root
```

#### Invalid Signature
```python
PermissionError: Token verification failed: Invalid signature or tampered payload
```

### 2. System Errors

#### Missing Token File
```
❌ [Shopping Agent] Error reading token: [Errno 2] No such file or directory: 'tokens.json'
```

#### MCP Server Connection Error
```python
httpx.ConnectError: [Errno 61] Connection refused - MCP server not running on localhost:8003
```

## Test Result Interpretation

### Exit Codes
- **0**: All tests passed successfully
- **1**: Some tests failed or system error occurred
- **2**: Blocked operation (for hook scenarios)

### Status Values
- **ALLOWED**: Operation permitted and executed
- **BLOCKED**: Operation denied due to scope violation
- **EXPIRED**: Operation denied due to token TTL expiry
- **ERROR**: System error during operation

### Performance Benchmarks
- **Latency**: < 100ms per operation under normal load
- **Throughput**: > 10 operations/second for stress testing  
- **Success Rate**: > 95% for valid operations
- **Security**: 100% blocking rate for unauthorized operations

## Demo Verification Checklist

When running the demo, verify these outputs appear:

- [ ] ✅ Coordinator successfully captures plan
- [ ] ✅ Multiple delegation tokens minted with different scopes
- [ ] ✅ Flight agent executes search_flights and book_flight (ALLOWED)
- [ ] ✅ Calendar agent executes read_events and delete_event (ALLOWED)  
- [ ] ✅ Shopping agent executes search_items and add_to_cart (ALLOWED)
- [ ] ✅ Shopping agent blocked from checkout (SCOPE VIOLATION)
- [ ] ✅ Shopping agent blocked after token expiry (EXPIRED)
- [ ] ✅ Audit dashboard shows all operations with correct statuses
- [ ] ✅ No unauthorized operations succeed

## Troubleshooting Common Issues

### 1. Port Conflicts
```bash
# Kill processes on demo ports
lsof -ti:8001,8002,8003,8501 | xargs kill -9 2>/dev/null
```

### 2. Database Lock Issues
```bash
# Remove database lock files
rm -f audit.db-wal audit.db-shm
```

### 3. Python Path Issues
```bash
# Ensure project root is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### 4. Missing Dependencies
```bash
# Install required packages
pip3 install -r requirements.txt
pip3 install pytest
```

## Conclusion

This test suite comprehensively validates Argus's core security features:

1. **Cryptographic Intent Verification**: Plans are captured with immutable intent records
2. **Scoped Delegation**: Tokens limit agent capabilities to specific tools  
3. **Time-Bounded Access**: TTL enforcement prevents token reuse attacks
4. **Tamper Detection**: HMAC signatures prevent token manipulation
5. **Audit Transparency**: Complete operation history with violation tracking

The output formats provide clear, structured data for both human operators and automated systems to verify proper governance enforcement across the multi-agent swarm.