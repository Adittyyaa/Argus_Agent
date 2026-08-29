#!/usr/bin/env python3
"""
main.py - Argus Multi-Agent Governance System
FastAPI app for Vercel deployment.
"""

import os
import sys
import json
import subprocess
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit.logger import AuditLogger
from mock_armoriq.client import ArmorIQClient

app = FastAPI(title="Argus Multi-Agent Governance System")

# Templates directory
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"))

logger = AuditLogger()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    stats = logger.get_stats()
    return templates.TemplateResponse("index.html", {"request": request, "stats": stats})


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "argus", "version": "1.0.0"}


@app.get("/api/stats")
async def get_stats():
    return logger.get_stats()


@app.get("/api/invocations")
async def get_invocations():
    return logger.get_invocations()


@app.get("/api/plans")
async def get_plans():
    return logger.get_plans()


@app.get("/api/delegations")
async def get_delegations():
    return logger.get_delegations()


@app.post("/api/run-demo")
async def run_demo(request: Request):
    body = await request.json()
    user_prompt = body.get("user_prompt", "Book me a flight to Delhi, clear my schedule on Thursday, and reorder headphones.")
    shopping_ttl = int(body.get("shopping_ttl", 10))
    pythonpath = ":".join(sys.path)
    env = {
        **os.environ,
        "PYTHONUNBUFFERED": "1",
        "SHOPPING_AGENT_TTL": str(shopping_ttl),
        "PYTHONPATH": pythonpath
    }
    root = os.path.dirname(os.path.abspath(__file__))

    result = subprocess.run(
        [sys.executable, "coordinator/main.py"],
        cwd=root, capture_output=True, text=True, env=env, timeout=60
    )
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode
    }


@app.post("/api/run-custom")
async def run_custom(request: Request):
    config = await request.json()
    root = os.path.dirname(os.path.abspath(__file__))

    if os.environ.get("VERCEL"):
        config_path = "/tmp/custom_config.json"
    else:
        config_path = os.path.join(root, "custom_config.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    pythonpath = ":".join(sys.path)
    env = {
        **os.environ,
        "PYTHONUNBUFFERED": "1",
        "PYTHONPATH": pythonpath
    }
    result = subprocess.run(
        [sys.executable, "custom_coordinator.py"],
        cwd=root, capture_output=True, text=True, env=env, timeout=120
    )
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode
    }


@app.post("/api/attack-sim")
async def attack_sim(request: Request):
    body = await request.json()
    sim_type = body.get("sim_type", "scope")

    import time
    client = ArmorIQClient(agent_id="attacker-subagent")
    output = []

    try:
        if sim_type == "scope":
            plan_id = client.capture_plan("Shopping intent", ["search_items", "add_to_cart"])
            token = client.delegate(plan_id=plan_id, sub_agent_id="attacker-subagent", scope=["search_items"], ttl_seconds=300)
            try:
                client.invoke(token=token, tool_name="checkout", args={"cart_id": "c1"}, execute_fn=lambda t, a: {"status": "success"})
                output.append({"type": "fail", "msg": "ATTACK SUCCEEDED — security check failed!"})
            except PermissionError as e:
                output.append({"type": "pass", "msg": f"ATTACK BLOCKED: {e}"})

        elif sim_type == "expiry":
            plan_id = client.capture_plan("Short plan", ["search_items"])
            token = client.delegate(plan_id=plan_id, sub_agent_id="attacker-subagent", scope=["search_items"], ttl_seconds=1)
            time.sleep(1.5)
            try:
                client.invoke(token=token, tool_name="search_items", args={}, execute_fn=lambda t, a: {"status": "success"})
                output.append({"type": "fail", "msg": "ATTACK SUCCEEDED — expiry check failed!"})
            except PermissionError as e:
                output.append({"type": "pass", "msg": f"EXPIRED TOKEN REJECTED: {e}"})

        elif sim_type == "forged":
            token = client.delegate(plan_id="plan-fake", sub_agent_id="attacker-subagent", scope=["search_items"], ttl_seconds=300)
            forged = token.split(".")[0] + ".fake_signature_abc123"
            try:
                client.invoke(token=forged, tool_name="search_items", args={}, execute_fn=lambda t, a: {"status": "success"})
                output.append({"type": "fail", "msg": "ATTACK SUCCEEDED — signature check failed!"})
            except PermissionError as e:
                output.append({"type": "pass", "msg": f"FORGED SIGNATURE REJECTED: {e}"})

    except Exception as e:
        output.append({"type": "error", "msg": str(e)})

    return {"results": output}
