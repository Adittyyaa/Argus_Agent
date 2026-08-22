"""
mcp_servers/calendar_mcp.py
===========================
MCP Server — Calendar Tools
Runs on http://localhost:8002

Tools exposed:
  • read_events(day)         → list calendar events for a day
  • delete_event(event_id)   → remove an event

Sub-agents call these via POST /tools/call. The ArmorIQ SDK governs
each call *before* it reaches these endpoints.
"""

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Dict

app = FastAPI(title="Calendar MCP Server", version="1.0.0")

PORT = 8002

# ── simulated calendar store ───────────────────────────────────────────
CALENDAR: Dict[str, list] = {
    "Monday":    [{"id": "evt-001", "title": "Team standup",        "time": "09:00", "duration": "30m"}],
    "Tuesday":   [{"id": "evt-002", "title": "Sprint planning",     "time": "10:00", "duration": "60m"}],
    "Wednesday": [{"id": "evt-003", "title": "1:1 with manager",    "time": "14:00", "duration": "30m"}],
    "Thursday": [
        {"id": "evt-004", "title": "Client demo",                   "time": "11:00", "duration": "90m"},
        {"id": "evt-005", "title": "Flight to Delhi (CONFLICT)",    "time": "15:30", "duration": "120m"},
    ],
    "Friday":    [{"id": "evt-006", "title": "Team retrospective",  "time": "16:00", "duration": "60m"}],
}

DELETED: Dict[str, dict] = {}  # track deleted events for audit

TOOLS = {
    "read_events": {
        "description": "List all calendar events for a given day",
        "parameters": {"day": "str"},
        "dangerous": False,
    },
    "delete_event": {
        "description": "Delete a calendar event by ID",
        "parameters": {"event_id": "str"},
        "dangerous": False,
    },
}


class ToolCallRequest(BaseModel):
    tool_name: str
    args: Dict[str, Any] = {}


@app.get("/tools")
def list_tools():
    return {"server": "calendar-mcp", "port": PORT, "tools": TOOLS}


@app.post("/tools/call")
def call_tool(req: ToolCallRequest):
    if req.tool_name == "read_events":
        return _read_events(**req.args)
    elif req.tool_name == "delete_event":
        return _delete_event(**req.args)
    else:
        return {"error": f"Unknown tool: {req.tool_name}", "available": list(TOOLS.keys())}


# ── tool implementations ───────────────────────────────────────────────

def _read_events(day: str = "Thursday") -> dict:
    day_title = day.title()
    events    = CALENDAR.get(day_title, [])
    return {
        "status": "ok",
        "day":    day_title,
        "events": events,
        "count":  len(events),
    }


def _delete_event(event_id: str) -> dict:
    for day, events in CALENDAR.items():
        for evt in events:
            if evt["id"] == event_id:
                CALENDAR[day].remove(evt)
                DELETED[event_id] = {**evt, "deleted_from": day}
                return {
                    "status":   "DELETED",
                    "event_id": event_id,
                    "title":    evt["title"],
                    "day":      day,
                    "message":  f"Event '{evt['title']}' on {day} at {evt['time']} has been removed",
                }
    return {
        "status":   "NOT_FOUND",
        "event_id": event_id,
        "message":  f"No event found with id: {event_id}",
    }


if __name__ == "__main__":
    print(f"[Calendar MCP] Starting on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")
