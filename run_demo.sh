#!/bin/bash

echo "========================================================="
echo "🚀 STARTING ARGUS HACKATHON DEMO"
echo "========================================================="

# 1. Kill any existing processes on our ports
echo "[1/4] Cleaning up old processes..."
lsof -ti:8001,8002,8003,8501 | xargs kill -9 2>/dev/null

# 2. Start MCP Servers in the background
echo "[2/4] Starting Mock MCP Servers (Ports 8001, 8002, 8003)..."
python3 mcp_servers/flight_mcp.py > /dev/null 2>&1 &
MCP1_PID=$!
python3 mcp_servers/calendar_mcp.py > /dev/null 2>&1 &
MCP2_PID=$!
python3 mcp_servers/shopping_mcp.py > /dev/null 2>&1 &
MCP3_PID=$!

# 3. Start Streamlit Dashboard in the background
echo "[3/4] Starting Streamlit Audit Dashboard (Port 8501)..."
python3 -m streamlit run dashboard/app.py --server.headless true --browser.gatherUsageStats false > /dev/null 2>&1 &
DASH_PID=$!

echo "⏳ Waiting for servers to initialize..."
sleep 3

# 4. Run the Coordinator (This drives the demo in the foreground)
echo "[4/4] Running Coordinator Agent..."
echo ""
python3 coordinator/main.py

echo ""
echo "========================================================="
echo "✅ DEMO COMPLETE!"
echo "The dashboard is still running at http://localhost:8501"
echo "Press Ctrl+C to stop all servers and exit."
echo "========================================================="

# Wait for user to Ctrl+C, then cleanup
trap "echo 'Shutting down...'; kill $MCP1_PID $MCP2_PID $MCP3_PID $DASH_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
