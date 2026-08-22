# AuthorChain Summary

This project implements a multi-agent "Personal Assistant Swarm" governed by a mocked version of the **ArmorIQ SDK**. 

It completely removes the need for API keys by simulating the LLM planning logic and using an offline mock of the ArmorIQ SDK (`mock_armoriq`), while perfectly capturing the architecture and security principles expected in the hackathon problem statement.

## Key Features

1. **Explicit Plans:** Coordinator records intent (`capture_plan`).
2. **Scoped Tokens:** Coordinator issues tokens (`delegate`) with specific scopes and short TTLs.
3. **Execution & Enforcement:** Sub-agents execute tools through `invoke`, which verifies the HMAC-signed token.
4. **Violation Demos:** Shopping agent attempts to use the `checkout` tool (Blocked - Scope Violation). Shopping agent tries again after a delay (Blocked - Token Expired).
5. **Audit Logging:** An SQLite DB acts as the immutable log, presented via a Streamlit Dashboard.

## Architecture

- **Coordinator** (`coordinator/main.py`): Parses user intent, plans, and spawns the delegation tree.
- **Agents** (`agents/*.py`): Separate Python processes simulating autonomous sub-agents with unique keypairs.
- **MCP Servers** (`mcp_servers/*.py`): Mock HTTP tool servers.
- **Audit System** (`audit/logger.py` + `dashboard/app.py`): Multi-process SQLite WAL database + UI.
- **ArmorIQ SDK Mock** (`mock_armoriq/client.py`): HMAC-signing token manager that enforces scope and expiry.

## Running in other agents

You can run this project offline. See `README.md` for startup commands. The core logic does not rely on external AI or ArmorIQ APIs, making it completely self-contained.
