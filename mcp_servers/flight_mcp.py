"""
mcp_servers/flight_mcp.py
=========================
MCP Server — Flight Tools
Runs on http://localhost:8001

Tools exposed:
  • search_flights(origin, destination, date) → list of available flights
  • book_flight(flight_id, passenger_name)    → booking confirmation

Sub-agents call these via POST /tools/call. The ArmorIQ SDK governs
each call *before* it reaches these endpoints.
"""

import random
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Dict

app = FastAPI(title="Flight MCP Server", version="1.0.0")

PORT = 8001

# ── tool schema (advertised to agents) ────────────────────────────────
TOOLS = {
    "search_flights": {
        "description": "Search available flights between two airports",
        "parameters": {"origin": "str", "destination": "str", "date": "str (optional)"},
        "dangerous": False,
    },
    "book_flight": {
        "description": "Confirm and book a specific flight",
        "parameters": {"flight_id": "str", "passenger_name": "str (optional)"},
        "dangerous": False,
    },
}


class ToolCallRequest(BaseModel):
    tool_name: str
    args: Dict[str, Any] = {}


@app.get("/tools")
def list_tools():
    """List all tools this MCP server exposes."""
    return {"server": "flight-mcp", "port": PORT, "tools": TOOLS}


@app.post("/tools/call")
def call_tool(req: ToolCallRequest):
    """Dispatch a tool call."""
    if req.tool_name == "search_flights":
        return _search_flights(**req.args)
    elif req.tool_name == "book_flight":
        return _book_flight(**req.args)
    else:
        return {"error": f"Unknown tool: {req.tool_name}", "available": list(TOOLS.keys())}


# ── tool implementations ───────────────────────────────────────────────

def _search_flights(origin: str = "BOM", destination: str = "DEL", date: str = "2026-09-01") -> dict:
    airlines = [
        {"id": "AI302",  "airline": "Air India",     "dep": "08:30", "arr": "10:45", "price": 4500, "seats": 12},
        {"id": "6E101",  "airline": "IndiGo",         "dep": "14:15", "arr": "16:20", "price": 3200, "seats": 5},
        {"id": "SG443",  "airline": "SpiceJet",       "dep": "20:00", "arr": "22:10", "price": 2800, "seats": 23},
        {"id": "UK987",  "airline": "Vistara",        "dep": "06:50", "arr": "08:55", "price": 5100, "seats": 8},
    ]
    return {
        "status": "ok",
        "from": origin,
        "to": destination,
        "date": date,
        "flights": airlines,
    }


def _book_flight(flight_id: str, passenger_name: str = "Hackathon User") -> dict:
    ref = f"BK{random.randint(100000, 999999)}"
    return {
        "status": "CONFIRMED",
        "booking_ref": ref,
        "flight_id": flight_id,
        "passenger": passenger_name,
        "seat": f"{random.randint(1, 30)}{random.choice('ABCDEF')}",
        "message": f"Flight {flight_id} booked for {passenger_name}. PNR: {ref}",
    }


if __name__ == "__main__":
    print(f"[Flight MCP] Starting on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")
