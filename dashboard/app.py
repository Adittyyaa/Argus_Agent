"""
dashboard/app.py
================
Argus Interactive GUI Audit & Multi-Agent Swarm Control Center.
Built with Streamlit for Microsoft Hackathon 2026.
"""

import os
import sys
import json
import time
import subprocess
import pandas as pd
import streamlit as st

# Fix SSL issues for cloud deployment
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from audit.logger import AuditLogger
from mock_armoriq.client import ArmorIQClient

# Page Config
st.set_page_config(
    page_title="Argus – ArmorIQ Personal Assistant Swarm",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add health check endpoint for cloud deployment
@st.cache_data
def health_check():
    return {"status": "healthy", "service": "argus"}

# Handle health check endpoint for Zop platform
try:
    if st.query_params.get("health") or "/healthz" in str(st.query_params):
        st.write({"status": "healthy", "service": "argus", "version": "1.0.0"})
        st.stop()
except:
    pass  # Ignore query param errors

# Custom Styling — Professional Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        background-color: #0b0f1a;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }
    section[data-testid="stSidebar"] {
        background-color: #0e1422;
        border-right: 1px solid rgba(148,163,184,0.12);
    }

    /* Metrics cards */
    [data-testid="stMetric"] {
        background: linear-gradient(180deg, #131b2e 0%, #0f1626 100%);
        border: 1px solid rgba(148,163,184,0.14);
        padding: 18px 22px;
        border-radius: 14px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.25);
        height: 100%;
        width: 100%;
    }
    [data-testid="stMetricLabel"] {
        color: #94a3b8;
        font-size: 0.82rem;
        letter-spacing: 0.02em;
    }
    [data-testid="stMetricValue"] {
        color: #f1f5f9;
        font-weight: 700;
    }
    /* Keep metric columns equal height & aligned */
    div[data-testid="stHorizontalBlock"] {
        align-items: stretch;
        gap: 1rem;
    }
    div[data-testid="stHorizontalBlock"] .element-container { height: 100%; }
    .metrics-row { margin-bottom: 1.75rem; }

    /* Hero banner */
    .hero {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 45%, #312e81 100%);
        border: 1px solid rgba(99,102,241,0.28);
        border-radius: 18px;
        padding: 1.75rem 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 12px 36px rgba(0,0,0,0.40);
    }
    .hero h1 {
        margin: 0;
        font-size: 1.9rem;
        font-weight: 700;
        color: #f8fafc;
        letter-spacing: -0.01em;
    }
    .hero .accent { color: #818cf8; }
    .hero p {
        margin: 0.5rem 0 0;
        color: #cbd5e1;
        font-size: 0.95rem;
        line-height: 1.5;
    }
    .hero .hero-sub {
        margin-top: 0.9rem;
        font-size: 0.82rem;
        color: #94a3b8;
        line-height: 1.45;
    }
    .hero .hero-list {
        margin: 1rem 0 0;
        padding-left: 1.1rem;
        color: #cbd5e1;
        font-size: 0.9rem;
        line-height: 1.7;
    }
    .hero .hero-list li { margin-bottom: 0.15rem; }
    .hero .hero-list b { color: #a5b4fc; }
    .hero .pill {
        display: inline-block;
        margin-top: 0.85rem;
        padding: 0.3rem 0.7rem;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: #a5b4fc;
        background: rgba(99,102,241,0.14);
        border: 1px solid rgba(99,102,241,0.35);
        border-radius: 999px;
    }

    /* Section headings */
    .section-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #e2e8f0;
        margin-bottom: 0.75rem;
    }

    /* Status colors */
    .status-allowed { color: #34d399; font-weight: 600; }
    .status-blocked { color: #f87171; font-weight: 600; }
    .status-expired { color: #fbbf24; font-weight: 600; }

    /* Terminal box */
    .terminal-box {
        font-family: 'JetBrains Mono', monospace;
        background: #050810;
        border: 1px solid rgba(99,102,241,0.30);
        padding: 16px;
        border-radius: 12px;
        color: #a5b4fc;
        line-height: 1.6;
        font-size: 0.85rem;
    }

    /* Info / architecture cards */
    .info-card {
        background: #0f1626;
        border: 1px solid rgba(148,163,184,0.14);
        border-radius: 14px;
        padding: 1.1rem 1.25rem;
        height: 100%;
    }
    .info-card h4 {
        margin: 0 0 0.6rem;
        font-size: 0.95rem;
        color: #e2e8f0;
        font-weight: 600;
    }
    .info-card ul { margin: 0; padding-left: 1.1rem; color: #cbd5e1; font-size: 0.86rem; line-height: 1.55; }
    .info-card li { margin-bottom: 0.35rem; }
    .info-card li b { color: #a5b4fc; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #0e1422;
        border-radius: 12px;
        padding: 5px;
        border: 1px solid rgba(148,163,184,0.12);
        gap: 6px;
        display: flex;
    }
    .stTabs [data-baseweb="tab"] {
        flex: 1 1 0;
        justify-content: center;
        border-radius: 9px;
        color: #94a3b8;
        font-weight: 500;
        transition: all 0.15s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #e2e8f0;
        background: rgba(148,163,184,0.06);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #4f46e5, #6366f1) !important;
        color: #ffffff !important;
    }

    .stDataFrame { border-radius: 12px; }
    div[data-testid="stExpander"] {
        border: 1px solid rgba(148,163,184,0.12);
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

logger = AuditLogger()

# ── Sidebar Configuration ──
with st.sidebar:
    st.title("Argus GUI")
    st.caption("Cryptographic Multi-Agent Governance")
    
    st.divider()
    
    # ArmorIQ API Connection Status
    api_key = os.getenv("ARMORIQ_API_KEY", "")
    mode = os.getenv("ARMORIQ_MODE", "mock").strip().lower()
    
    if api_key and api_key.startswith("ak_"):
        st.success("ArmorIQ Cloud API Connected")
        st.caption(f"**Endpoint:** `platform.armoriq.ai`  \n**Key:** `{api_key[:10]}...{api_key[-4:]}`")
    else:
        st.info("ArmorIQ Local Mock Mode")
        st.caption("Running local HMAC verification.")
        st.caption(f"**Deployed from:** https://github.com/Adittyyaa/Argus_Agent")
        
    st.divider()
    
    st.subheader("Quick Settings")
    auto_refresh = st.checkbox("Auto-refresh Audit Trail (3s)", value=False)
    
    if auto_refresh:
        time.sleep(3)
        st.rerun()

# ── Main Header ──
st.markdown("""
<div class="hero">
    <h1>Argus <span class="accent">Control Center</span> &amp; Audit Dashboard</h1>
    <p><b>What it does:</b> Argus coordinates AI agents and issues each one a scoped,
       cryptographically-signed token &mdash; so agents can only run approved tools,
       actions are enforced in real time, and every decision is logged and auditable.</p>
    <ul class="hero-list">
        <li><b>Plan</b> &mdash; the Coordinator records user intent before any agent acts.</li>
        <li><b>Delegate</b> &mdash; each sub-agent gets a short-lived, scoped HMAC token (least privilege).</li>
        <li><b>Enforce</b> &mdash; every tool call is verified for scope, signature, and expiry before execution.</li>
        <li><b>Audit</b> &mdash; a tamper-evident log records every ALLOWED, BLOCKED, and EXPIRED decision.</li>
    </ul>
    <p class="hero-sub">A Personal Assistant Swarm protected by cryptographic intent
       verification via the <b>ArmorIQ SDK</b> &mdash; every agent action is scoped, signed, and audited.</p>
    <span class="pill">Zero-Trust Multi-Agent Governance</span>
</div>
""", unsafe_allow_html=True)

# ── Top Metrics Row (always visible) ──
stats = logger.get_stats()
st.markdown('<div class="metrics-row">', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Tool Invocations", stats["total"])
c2.metric("Authorized", stats["allowed"])
c3.metric("Blocked (Scope Violation)", stats["blocked"])
c4.metric("Expired (TTL Timeout)", stats["expired"])
st.markdown('</div>', unsafe_allow_html=True)

# ── Tabs ──
tab1, tab2, tab3, tab4 = st.tabs([
    "Real-Time Audit Trail",
    "Run Swarm Demo",
    "Custom Agent Control",
    "Red-Team Attack Simulator"
])

# ── TAB 1: Real-Time Audit Trail ──
with tab1:
    st.subheader("Live Invocations Log")
    invocations = logger.get_invocations()

    if invocations:
        df_inv = pd.DataFrame(invocations)
        
        # Filter options
        status_filter = st.multiselect(
            "Filter by Status",
            options=["ALLOWED", "BLOCKED", "EXPIRED", "ERROR"],
            default=["ALLOWED", "BLOCKED", "EXPIRED", "ERROR"]
        )
        
        filtered_df = df_inv[df_inv["status"].isin(status_filter)]
        
        def highlight_status(row):
            val = row['status']
            if val == 'ALLOWED':
                return ['background-color: rgba(0, 212, 170, 0.15)'] * len(row)
            elif val == 'BLOCKED':
                return ['background-color: rgba(255, 107, 107, 0.2)'] * len(row)
            elif val == 'EXPIRED':
                return ['background-color: rgba(255, 209, 102, 0.2)'] * len(row)
            return [''] * len(row)

        st.dataframe(
            filtered_df[["timestamp", "status", "agent_id", "tool_name", "reason", "ttl_remaining"]].style.apply(highlight_status, axis=1),
            use_container_width=True,
            hide_index=True,
            height=300
        )
    else:
        st.info("No tool invocations recorded yet. Click **Run Swarm Demo** to generate events.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Captured Plans (capture_plan)")
        plans = logger.get_plans()
        if plans:
            st.dataframe(pd.DataFrame(plans)[["plan_id", "description", "declared_tools", "user_email"]], use_container_width=True, hide_index=True)
        else:
            st.caption("No plans recorded.")

    with col2:
        st.subheader("Issued Delegation Tokens (delegate)")
        dels = logger.get_delegations()
        if dels:
            st.dataframe(pd.DataFrame(dels)[["delegation_id", "agent_id", "scope", "ttl_seconds", "issued_by"]], use_container_width=True, hide_index=True)
        else:
            st.caption("No delegation tokens recorded.")


# ── TAB 2: Run Swarm Demo ──
with tab2:
    st.subheader("Execute Swarm Demo from GUI")
    st.markdown("Run the full multi-agent workflow: Coordinator -> Flight Agent -> Calendar Agent -> Shopping Agent.")
    
    col_input, col_ttl = st.columns([3, 1])
    with col_input:
        user_prompt = st.text_input("User Prompt Intent", value="Book me a flight to Delhi, clear my schedule on Thursday, and reorder headphones.")
    with col_ttl:
        shopping_ttl_setting = st.slider("Shopping Agent TTL (sec)", min_value=2, max_value=30, value=10)

    if st.button("Launch Multi-Agent Swarm Demo", type="primary"):
        os.environ["SHOPPING_AGENT_TTL"] = str(shopping_ttl_setting)
        
        with st.spinner("Executing Swarm Coordinator & Sub-Agents..."):
            log_container = st.empty()
            
            # Execute coordinator
            result = subprocess.run(
                [sys.executable, "coordinator/main.py"],
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                capture_output=True,
                text=True,
                env={**os.environ, "PYTHONUNBUFFERED": "1"}
            )
            
            st.markdown("### Swarm Live Terminal Execution Log")
            st.code(result.stdout, language="bash")
            if result.stderr:
                st.warning("Errors/Warnings:")
                st.code(result.stderr, language="bash")
                
        st.success("Demo Completed! Check the **Real-Time Audit Trail** tab to view updated logs.")
        st.rerun()


# ── TAB 3: Custom Agent Control ──
with tab3:
    st.subheader("Custom Agent Control Panel")
    st.markdown("**Interactive GUI to control individual agents with custom commands and permissions**")
    
    # Quick Start Demo
    with st.expander("Quick Start Demo Examples", expanded=False):
        st.markdown("""
        **Try these example scenarios:**
        
        1. **Basic Travel Planning:**
           - Intent: *"Book me a flight to Paris and clear my schedule"*
           - Give flight agent: `search_flights`, `book_flight`
           - Give calendar agent: `read_events`, `delete_event`
        
        2. **Shopping with Security Test:**
           - Intent: *"Find and buy headphones under $100"*
           - Give shopping agent: `search_items`, `add_to_cart` (but NOT `checkout`)
           - Enable "Test Scope Violation" to see security enforcement
        
        3. **Full Permissions Test:**
           - Intent: *"Complete travel and shopping for business trip"*
           - Give all agents full permissions and see the difference
           
        4. **Token Expiry Demo:**
           - Set shopping agent TTL to 5 seconds
           - Enable "Test Token Expiry" 
           - Watch tokens expire and get rejected
        """)
    
    st.divider()
    
    # Custom User Intent
    st.markdown("### Custom User Intent")
    col_intent, col_user = st.columns([3, 1])
    with col_intent:
        custom_prompt = st.text_area(
            "Enter your custom command:", 
            value="Book me a flight to Tokyo, schedule a meeting with the team, and order a new laptop",
            height=100,
            help="Describe what you want the AI agents to accomplish"
        )
    with col_user:
        user_email = st.text_input("User Email:", value="demo@company.com")
    
    # Available Tools Configuration
    st.markdown("### Available Tools Configuration")
    st.caption("Select which tools are available in the system (this sets the global tool scope)")
    
    available_tools = st.multiselect(
        "Available Tools:",
        options=[
            "search_flights", "book_flight", "cancel_flight",
            "read_events", "create_event", "delete_event", "update_event", 
            "search_items", "add_to_cart", "checkout", "track_order",
            "send_email", "read_inbox", "schedule_meeting",
            "make_payment", "check_balance", "transfer_funds"
        ],
        default=["search_flights", "book_flight", "read_events", "delete_event", "search_items", "add_to_cart"],
        help="These are all the tools that agents can potentially use"
    )
    
    # Individual Agent Configuration
    st.markdown("### Individual Agent Configuration")
    
    # Flight Agent
    with st.expander("✈️ Flight Agent Configuration", expanded=True):
        col_flight_scope, col_flight_ttl, col_flight_args = st.columns([2, 1, 2])
        
        with col_flight_scope:
            flight_scope = st.multiselect(
                "Flight Agent Permissions:",
                options=[tool for tool in available_tools if "flight" in tool or "search_flights" in tool or "book_flight" in tool],
                default=["search_flights", "book_flight"] if "search_flights" in available_tools else [],
                help="What this agent is allowed to do"
            )
        
        with col_flight_ttl:
            flight_ttl = st.number_input("TTL (seconds):", min_value=10, max_value=3600, value=300, key="flight_ttl")
        
        with col_flight_args:
            flight_origin = st.text_input("Origin:", value="NYC", key="flight_origin")
            flight_dest = st.text_input("Destination:", value="TOK", key="flight_dest")
            passenger_name = st.text_input("Passenger:", value="Demo User", key="passenger")
    
    # Calendar Agent  
    with st.expander("📅 Calendar Agent Configuration"):
        col_cal_scope, col_cal_ttl, col_cal_args = st.columns([2, 1, 2])
        
        with col_cal_scope:
            calendar_scope = st.multiselect(
                "Calendar Agent Permissions:",
                options=[tool for tool in available_tools if "event" in tool or "calendar" in tool or "meeting" in tool],
                default=["read_events", "delete_event"] if "read_events" in available_tools else [],
                help="What this agent is allowed to do"
            )
        
        with col_cal_ttl:
            calendar_ttl = st.number_input("TTL (seconds):", min_value=10, max_value=3600, value=300, key="cal_ttl")
            
        with col_cal_args:
            event_title = st.text_input("Event Title:", value="Team Meeting", key="event_title")
            event_date = st.text_input("Event Date:", value="Thursday", key="event_date")
    
    # Shopping Agent
    with st.expander("🛒 Shopping Agent Configuration"):
        col_shop_scope, col_shop_ttl, col_shop_args = st.columns([2, 1, 2])
        
        with col_shop_scope:
            shopping_scope = st.multiselect(
                "Shopping Agent Permissions:",
                options=[tool for tool in available_tools if any(word in tool for word in ["item", "cart", "checkout", "order", "shop"])],
                default=["search_items", "add_to_cart"] if "search_items" in available_tools else [],
                help="What this agent is allowed to do (notice checkout is optional)"
            )
        
        with col_shop_ttl:
            shopping_ttl = st.number_input("TTL (seconds):", min_value=5, max_value=3600, value=15, key="shop_ttl")
            
        with col_shop_args:
            search_query = st.text_input("Search Query:", value="wireless headphones", key="search_query") 
            max_price = st.number_input("Max Price:", min_value=0, max_value=10000, value=200, key="max_price")
    
    # Security Testing Options
    st.markdown("### 🔒 Security Testing Options")
    col_sec1, col_sec2 = st.columns(2)
    
    with col_sec1:
        test_scope_violation = st.checkbox("🚨 Test Scope Violation", help="Shopping agent will try to use 'checkout' even if not in scope")
        test_token_expiry = st.checkbox("⏰ Test Token Expiry", help="Agents will wait and try operations after TTL expires")
        
    with col_sec2:
        include_unauthorized_tools = st.checkbox("🔓 Include Unauthorized Tools", help="Add tools that agents will try to use without permission")
        simulate_attacks = st.checkbox("⚔️ Simulate Attack Scenarios", help="Test various security attack patterns")
    
    # Execute Button
    st.markdown("### 🚀 Execute Custom Scenario")
    
    if st.button("▶️ Run Custom Agent Scenario", type="primary", key="custom_run"):
        if not available_tools:
            st.error("❌ Please select at least one available tool")
        elif not any([flight_scope, calendar_scope, shopping_scope]):
            st.error("❌ Please give at least one agent some permissions")
        else:
            # Create custom configuration
            custom_config = {
                "user_intent": custom_prompt,
                "user_email": user_email,
                "available_tools": available_tools,
                "agents": {
                    "flight": {
                        "scope": flight_scope,
                        "ttl": flight_ttl,
                        "args": {
                            "origin": flight_origin,
                            "destination": flight_dest,
                            "passenger_name": passenger_name
                        }
                    },
                    "calendar": {
                        "scope": calendar_scope, 
                        "ttl": calendar_ttl,
                        "args": {
                            "event_title": event_title,
                            "event_date": event_date
                        }
                    },
                    "shopping": {
                        "scope": shopping_scope,
                        "ttl": shopping_ttl,
                        "args": {
                            "search_query": search_query,
                            "max_price": max_price
                        }
                    }
                },
                "security_tests": {
                    "scope_violation": test_scope_violation,
                    "token_expiry": test_token_expiry,
                    "unauthorized_tools": include_unauthorized_tools,
                    "simulate_attacks": simulate_attacks
                }
            }
            
            # Save configuration — use absolute path so custom_coordinator finds it
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "custom_config.json")
            with open(config_path, "w") as f:
                json.dump(custom_config, f, indent=2)
            
            with st.spinner("🚀 Executing custom agent scenario..."):
                log_container = st.empty()
                
                # Execute custom coordinator
                result = subprocess.run(
                    [sys.executable, "custom_coordinator.py"],
                    cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    capture_output=True,
                    text=True,
                    env={**os.environ, "PYTHONUNBUFFERED": "1"}
                )
                
                st.markdown("### 🖥️ Custom Scenario Execution Log")
                if result.stdout:
                    st.code(result.stdout, language="bash")
                if result.stderr:
                    st.warning("Errors/Warnings:")
                    st.code(result.stderr, language="bash")
                    
                if result.returncode == 0:
                    st.success("✅ Custom scenario completed successfully!")
                else:
                    st.error(f"❌ Scenario failed with exit code {result.returncode}")
                    
            st.rerun()


# ── TAB 4: Red-Team Attack Simulator ──
with tab4:
    st.subheader("🛡️ Interactive Security Attack & Governance Simulator")
    st.markdown("Test ArmorIQ's enforcement engine directly by simulating attacks against sub-agent tokens.")
    
    sim_type = st.radio(
        "Select Attack Scenario to Simulate:",
        ["1. Scope Violation (Rogue Tool Call)", "2. Token Expiry Attempt", "3. Forged HMAC Signature Attack"]
    )
    
    if st.button("⚡ Execute Attack Simulation"):
        sim_client = ArmorIQClient(agent_id="attacker-subagent")
        
        if "Scope Violation" in sim_type:
            plan_id = sim_client.capture_plan("Shopping intent", ["search_items", "add_to_cart"])
            token = sim_client.delegate(plan_id=plan_id, sub_agent_id="attacker-subagent", scope=["search_items"], ttl_seconds=300)
            
            st.info("Simulating unauthorized tool call: `checkout` (not in scope `['search_items']`)...")
            try:
                sim_client.invoke(token=token, tool_name="checkout", args={"cart_id": "c1"}, execute_fn=lambda t, a: {"status": "success"})
                st.error("❌ Attack Succeeded (FAILED Security Check!)")
            except PermissionError as pe:
                st.success(f"✅ **ATTACK BLOCKED BY ARMORIQ!**  \n`{pe}`")
                
        elif "Token Expiry" in sim_type:
            plan_id = sim_client.capture_plan("Short plan", ["search_items"])
            token = sim_client.delegate(plan_id=plan_id, sub_agent_id="attacker-subagent", scope=["search_items"], ttl_seconds=1)
            
            st.info("Waiting 1.5 seconds for token TTL to expire...")
            time.sleep(1.5)
            
            try:
                sim_client.invoke(token=token, tool_name="search_items", args={}, execute_fn=lambda t, a: {"status": "success"})
                st.error("❌ Attack Succeeded (FAILED Expiry Check!)")
            except PermissionError as pe:
                st.success(f"✅ **EXPIRED TOKEN REJECTED BY ARMORIQ!**  \n`{pe}`")
                
        elif "Forged HMAC" in sim_type:
            valid_token = sim_client.delegate(plan_id="plan-fake", sub_agent_id="attacker-subagent", scope=["search_items"], ttl_seconds=300)
            forged_token = valid_token.split(".")[0] + ".fake_signature_abc123"
            
            st.info("Attempting call with tampered HMAC signature...")
            try:
                sim_client.invoke(token=forged_token, tool_name="search_items", args={}, execute_fn=lambda t, a: {"status": "success"})
                st.error("❌ Attack Succeeded (FAILED Signature Check!)")
            except PermissionError as pe:
                st.success(f"✅ **FORGED SIGNATURE REJECTED BY ARMORIQ!**  \n`{pe}`")

        st.rerun()


# ── Architecture & Security Model (main page) ──
with st.expander("Architecture & Security Model", expanded=False):
    st.markdown('<div class="section-title">How Argus enforces zero-trust governance</div>', unsafe_allow_html=True)
    arch_c1, arch_c2 = st.columns([1, 1])
    with arch_c1:
        st.markdown("""
        <div class="info-card">
            <h4>Key Innovations</h4>
            <ul>
                <li><b>Cryptographic Delegation Chain</b> &mdash; scoped, signed HMAC tokens per sub-agent keypair.</li>
                <li><b>Runtime Enforcement (<code>invoke</code>)</b> &mdash; cryptographically validates tool name, TTL, and signature before reaching MCP servers.</li>
                <li><b>ArmorIQ Cloud Integration</b> &mdash; issues Merkle step proof tokens via <code>platform.armoriq.ai</code>.</li>
                <li><b>Zero-Trust Audit Trail</b> &mdash; immutable SQLite database recording every <code>ALLOWED</code>, <code>BLOCKED</code>, and <code>EXPIRED</code> decision.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    with arch_c2:
        st.markdown("""
        <div class="info-card">
            <h4>Technology Stack</h4>
            <ul>
                <li><b>Governance</b> &mdash; ArmorIQ SDK (<code>armoriq-sdk</code>)</li>
                <li><b>Backend</b> &mdash; Python 3.13 + FastAPI + Uvicorn</li>
                <li><b>Audit Layer</b> &mdash; SQLite WAL multi-process DB + Streamlit</li>
                <li><b>Tool Servers</b> &mdash; Mock HTTP MCP servers (ports 8001, 8002, 8003)</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
