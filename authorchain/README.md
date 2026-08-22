# AuthorChain

A multi-agent Personal Assistant Swarm protected by cryptographic intent verification. Built for the Microsoft Hackathon 2026.

## How to run locally

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Start the Mock MCP Servers (Background)**
Open a separate terminal for each:
```bash
python mcp_servers/flight_mcp.py
python mcp_servers/calendar_mcp.py
python mcp_servers/shopping_mcp.py
```

**3. Run the Dashboard**
Open a new terminal and run:
```bash
streamlit run dashboard/app.py
```

**4. Run the Coordinator (The Demo)**
Run the main pipeline in a new terminal:
```bash
python coordinator/main.py
```

You will see:
1. The coordinator minting tokens.
2. The sub-agents executing their allowed tasks.
3. The shopping agent being BLOCKED when attempting to checkout.
4. The shopping agent being BLOCKED due to EXPIRED token on its final request.
5. Watch the dashboard update live!
