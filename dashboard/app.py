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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from audit.logger import AuditLogger
from mock_armoriq.client import ArmorIQClient

# Page Config
st.set_page_config(
    page_title="Argus – ArmorIQ Personal Assistant Swarm",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    .stMetric { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); padding: 12px 18px; border-radius: 12px; }
    .status-allowed { color: #00d4aa; font-weight: 600; }
    .status-blocked { color: #ff6b6b; font-weight: 600; }
    .status-expired { color: #ffd166; font-weight: 600; }
    .terminal-box { font-family: 'JetBrains Mono', monospace; background: #050810; border: 1px solid rgba(108,99,255,0.3); padding: 15px; border-radius: 10px; color: #a29bff; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

logger = AuditLogger()

# ── Sidebar Configuration ──
with st.sidebar:
    st.image("https://img.icons8.com/isometric-folders/100/security-shield.png", width=64)
    st.title("Argus GUI")
    st.caption("Cryptographic Multi-Agent Governance")
    
    st.divider()
    
    # ArmorIQ API Connection Status
    api_key = os.getenv("ARMORIQ_API_KEY", "")
    mode = os.getenv("ARMORIQ_MODE", "mock").strip().lower()
    
    if api_key and api_key.startswith("ak_"):
        st.success("🔒 **ArmorIQ Cloud API Connected**")
        st.caption(f"**Endpoint:** `platform.armoriq.ai`  \n**Key:** `{api_key[:10]}...{api_key[-4:]}`")
    else:
        st.info("⚡ **ArmorIQ Local Mock Mode**")
        st.caption("Running local HMAC verification.")
        
    st.divider()
    
    st.subheader("⚙️ Quick Settings")
    auto_refresh = st.checkbox("Auto-refresh Audit Trail (3s)", value=False)
    
    if auto_refresh:
        time.sleep(3)
        st.rerun()

# ── Main Header ──
st.title("🛡️ Argus Control Center & Audit Dashboard")
st.markdown(
    "A Personal Assistant Swarm protected by cryptographic intent verification via the **ArmorIQ SDK**."
)

# ── Tabs ──
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Real-Time Audit Trail",
    "🚀 Run Swarm Demo",
    "🛡️ Red-Team Attack Simulator",
    "📈 Hackathon Slides & Architecture"
])

# ── TAB 1: Real-Time Audit Trail ──
with tab1:
    stats = logger.get_stats()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Tool Invocations", stats["total"])
    c2.metric("✅ Authorized", stats["allowed"])
    c3.metric("❌ Blocked (Scope Violation)", stats["blocked"])
    c4.metric("⚠️ Expired (TTL Timeout)", stats["expired"])

    st.subheader("📜 Live Invocations Log")
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
        st.subheader("📌 Captured Plans (capture_plan)")
        plans = logger.get_plans()
        if plans:
            st.dataframe(pd.DataFrame(plans)[["plan_id", "description", "declared_tools", "user_email"]], use_container_width=True, hide_index=True)
        else:
            st.caption("No plans recorded.")

    with col2:
        st.subheader("🔑 Issued Delegation Tokens (delegate)")
        dels = logger.get_delegations()
        if dels:
            st.dataframe(pd.DataFrame(dels)[["delegation_id", "agent_id", "scope", "ttl_seconds", "issued_by"]], use_container_width=True, hide_index=True)
        else:
            st.caption("No delegation tokens recorded.")


# ── TAB 2: Run Swarm Demo ──
with tab2:
    st.subheader("🚀 Execute Swarm Demo from GUI")
    st.markdown("Run the full multi-agent workflow: Coordinator -> Flight Agent -> Calendar Agent -> Shopping Agent.")
    
    col_input, col_ttl = st.columns([3, 1])
    with col_input:
        user_prompt = st.text_input("User Prompt Intent", value="Book me a flight to Delhi, clear my schedule on Thursday, and reorder headphones.")
    with col_ttl:
        shopping_ttl_setting = st.slider("Shopping Agent TTL (sec)", min_value=2, max_value=30, value=10)

    if st.button("▶️ Launch Multi-Agent Swarm Demo", type="primary"):
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
            
            st.markdown("### 🖥️ Swarm Live Terminal Execution Log")
            st.code(result.stdout, language="bash")
            if result.stderr:
                st.warning("Errors/Warnings:")
                st.code(result.stderr, language="bash")
                
        st.success("✅ Demo Completed! Check the **Real-Time Audit Trail** tab to view updated logs.")
        st.rerun()


# ── TAB 3: Red-Team Attack Simulator ──
with tab3:
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


# ── TAB 4: Hackathon Slides & Architecture ──
with tab4:
    st.subheader("📜 Argus Architecture & Hackathon Presentation")
    
    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.markdown("""
        ### 🔑 Key Innovations
        1. **Cryptographic Delegation Chain**: Scoped, signed HMAC tokens per sub-agent keypair.
        2. **Runtime Enforcement (`invoke`)**: Cryptographically validates tool name, TTL, and signature before reaching MCP servers.
        3. **ArmorIQ Cloud Integration**: Integrates directly with `platform.armoriq.ai` to issue Merkle step proof tokens.
        4. **Zero-Trust Audit Trail**: Immutable SQLite database recording every `ALLOWED`, `BLOCKED`, and `EXPIRED` decision.
        """)
        
    with col_b:
        st.markdown("""
        ### 🛠️ Technology Stack
        * **Governance**: ArmorIQ SDK (`armoriq-sdk`)
        * **Backend**: Python 3.13 + FastAPI + Uvicorn
        * **Audit Layer**: SQLite WAL Multi-Process DB + Streamlit
        * **Tool Servers**: Mock HTTP MCP Servers (Ports 8001, 8002, 8003)
        """)

    st.divider()
    st.info("💡 To view the full animated 7-slide Hackathon Presentation, open `presentation.html` in your browser.")
