"""
mcp_servers/shopping_mcp.py
===========================
MCP Server — Shopping Tools
Runs on http://localhost:8003

Tools exposed:
  • search_items(query)       → list matching products
  • add_to_cart(item_id, qty) → update cart
  • checkout(cart_id)         → DANGEROUS! finalizing purchase

Sub-agents call these via POST /tools/call. The ArmorIQ SDK governs
each call *before* it reaches these endpoints.
"""

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Dict

app = FastAPI(title="Shopping MCP Server", version="1.0.0")
PORT = 8003

# ── simulated store ───────────────────────────────────────────
INVENTORY = [
    {"id": "itm-01", "name": "Sony WH-1000XM5 Headphones", "price": 350.00, "stock": 14},
    {"id": "itm-02", "name": "USB-C to USB-C Cable 2m",    "price": 15.00,  "stock": 105},
    {"id": "itm-03", "name": "Logitech MX Master 3S",      "price": 99.00,  "stock": 22},
]

CART = {"cart-99": {"items": [], "total": 0.0}}

TOOLS = {
    "search_items": {
        "description": "Search inventory for products",
        "parameters": {"query": "str"},
        "dangerous": False,
    },
    "add_to_cart": {
        "description": "Add a product to the shopping cart",
        "parameters": {"item_id": "str", "qty": "int"},
        "dangerous": False,
    },
    "checkout": {
        "description": "Process payment and checkout the cart. DANGEROUS.",
        "parameters": {"cart_id": "str"},
        "dangerous": True,
    },
}

class ToolCallRequest(BaseModel):
    tool_name: str
    args: Dict[str, Any] = {}

@app.get("/tools")
def list_tools():
    return {"server": "shopping-mcp", "port": PORT, "tools": TOOLS}

@app.post("/tools/call")
def call_tool(req: ToolCallRequest):
    if req.tool_name == "search_items":
        return _search_items(**req.args)
    elif req.tool_name == "add_to_cart":
        return _add_to_cart(**req.args)
    elif req.tool_name == "checkout":
        return _checkout(**req.args)
    else:
        return {"error": f"Unknown tool: {req.tool_name}", "available": list(TOOLS.keys())}

# ── tool implementations ───────────────────────────────────────────────

def _search_items(query: str) -> dict:
    q = query.lower()
    results = [i for i in INVENTORY if q in i["name"].lower()]
    return {"status": "ok", "query": query, "results": results}

def _add_to_cart(item_id: str, qty: int = 1) -> dict:
    item = next((i for i in INVENTORY if i["id"] == item_id), None)
    if not item:
        return {"status": "error", "message": "Item not found"}
    CART["cart-99"]["items"].append({"item": item["name"], "qty": qty})
    CART["cart-99"]["total"] += item["price"] * qty
    return {"status": "ADDED", "cart": CART["cart-99"]}

def _checkout(cart_id: str) -> dict:
    if cart_id not in CART:
        return {"status": "error", "message": "Cart not found"}
    cart = CART[cart_id]
    if not cart["items"]:
        return {"status": "error", "message": "Cart is empty"}
    
    total = cart["total"]
    # Simulate emptying cart after purchase
    CART[cart_id] = {"items": [], "total": 0.0}
    return {
        "status": "PURCHASE_COMPLETE",
        "amount_charged": total,
        "message": f"Successfully charged ${total:.2f} to saved payment method.",
    }

if __name__ == "__main__":
    print(f"[Shopping MCP] Starting on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")
