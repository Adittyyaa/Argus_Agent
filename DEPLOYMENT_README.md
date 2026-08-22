# Argus - Multi-Agent Governance System

## Quick Start (5 minutes)

### Prerequisites
- Docker Desktop installed and running
- MacOS, Linux, or Windows with WSL2

### 1. Deploy in One Command
```bash
# Extract the zip file and navigate to the directory
cd argus

# Deploy everything with one command
./docker-deploy.sh start
```

### 2. Run the Demo
```bash
# In the same terminal or a new one
./docker-deploy.sh demo
```

### 3. View Results
- **Dashboard**: http://localhost:8501 (Audit logs and governance overview)
- **Console**: See real-time governance output in your terminal

## What You'll See

### Console Output
```
[ArmorIQ] ┌── capture_plan ──────────────────────────────────────
[ArmorIQ] │  plan_id : plan-c144145f82
[ArmorIQ] │  intent  : Book me a flight to Delhi, clear my schedule
[ArmorIQ] │  tools   : ['search_flights', 'book_flight', 'read_events']
[ArmorIQ] └─────────────────────────────────────────────────────

[ArmorIQ] delegate() → agent-flight-001
           scope     : ['search_flights', 'book_flight']
           ttl       : 300s  expires: 03:46:41

[ArmorIQ] invoke() ▶  tool=search_flights  agent=agent-flight-001
[ArmorIQ]   ✓ AUTHORIZED  scope=['search_flights', 'book_flight']

[ArmorIQ] invoke() ▶  tool=checkout  agent=agent-shopping-003
[ArmorIQ]   ✗ SCOPE VIOLATION
```

### Web Dashboard
- Real-time audit logs
- Security violations tracking
- Agent operation monitoring
- Governance analytics

## System Architecture

Argus demonstrates:
- **Cryptographic Intent Verification** - HMAC-signed delegation tokens
- **Scoped Agent Authorization** - Agents can only use approved tools
- **Time-Bounded Access Control** - Tokens expire automatically
- **Complete Audit Trail** - Every operation logged immutably
- **Zero-Trust Security** - Block-by-default security model

## Services Deployed

| Service | Port | Purpose |
|---------|------|---------|
| Dashboard | 8501 | Streamlit audit interface |
| Coordinator | 8000 | Main governance engine |
| Flight MCP | 8001 | Mock flight booking service |
| Calendar MCP | 8002 | Mock calendar service |
| Shopping MCP | 8003 | Mock shopping service |

## Management Commands

```bash
# Deploy/start all services
./docker-deploy.sh start

# Run the governance demo
./docker-deploy.sh demo

# Check service status
./docker-deploy.sh status

# View logs
./docker-deploy.sh logs

# Stop all services
./docker-deploy.sh stop

# Interactive menu
./docker-deploy.sh
```

## Test the System

```bash
# Run comprehensive test suite
python3 run_tests.py

# Or run specific tests
python3 -m pytest tests/ -v
```

## Troubleshooting

### Port Conflicts
```bash
# Kill processes using the ports
lsof -ti:8000,8001,8002,8003,8501 | xargs kill -9

# Or use the cleanup command
./docker-deploy.sh cleanup
```

### Docker Issues
```bash
# Restart Docker Desktop from menu bar
# Or restart services
docker-compose restart
```

### Permission Issues
```bash
# Make scripts executable
chmod +x docker-deploy.sh run_demo.sh
```

## What This Demonstrates

This is a production-ready multi-agent governance system that:

1. **Captures user intent** as immutable plans
2. **Mints cryptographic tokens** with specific tool permissions
3. **Enforces security boundaries** between agents
4. **Prevents unauthorized operations** through scope checking
5. **Implements time-bounded access** via token TTL
6. **Logs every operation** for compliance and audit
7. **Provides real-time monitoring** through web dashboard

The system shows how to build secure, auditable AI agent systems that can be trusted in production environments.

## Business Value

- **Compliance Ready**: Complete audit trails for regulatory requirements
- **Security First**: Multiple layers of protection against unauthorized actions
- **Scalable**: Handles concurrent operations efficiently  
- **Transparent**: Clear logging and monitoring capabilities
- **Zero Trust**: Every operation verified regardless of source

## Next Steps

1. Review the code in `agents/`, `coordinator/`, and `audit/` directories
2. Examine the test cases in `tests/` for security validation
3. Customize the agents for your specific use cases
4. Deploy to production infrastructure using the Docker containers

This system is ready for production deployment and can be extended with additional agents, tools, and governance policies.