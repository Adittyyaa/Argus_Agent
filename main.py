#!/usr/bin/env python3
"""
main.py
=======
FastAPI wrapper for Streamlit app to work with Vercel
"""

import os
import sys
import subprocess
import time
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

# Create FastAPI app for Vercel compatibility
app = FastAPI(title="Argus Multi-Agent Governance System")

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

@app.get("/")
async def root():
    """Root endpoint - shows Argus info"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Argus - Multi-Agent Governance System</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            .header { text-align: center; margin-bottom: 40px; }
            .feature { margin: 20px 0; padding: 15px; border-left: 4px solid #6366f1; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🛡️ Argus Multi-Agent Governance System</h1>
            <p>Cryptographic intent verification for AI agents</p>
        </div>
        
        <div class="feature">
            <h3>🔑 Key Features</h3>
            <ul>
                <li>Cryptographic delegation tokens with HMAC signatures</li>
                <li>Scoped agent authorization with strict scope enforcement</li>
                <li>Time-bounded access control with automatic token expiry</li>
                <li>Complete audit trail with immutable database logging</li>
                <li>Interactive GUI for custom agent control</li>
            </ul>
        </div>
        
        <div class="feature">
            <h3>🚀 Repository</h3>
            <p><a href="https://github.com/Adittyyaa/Argus_Agent">https://github.com/Adittyyaa/Argus_Agent</a></p>
        </div>
        
        <div class="feature">
            <h3>📊 Demo</h3>
            <p>This is a production-ready multi-agent governance system demonstrating:</p>
            <ul>
                <li>Security violations correctly blocked (scope + TTL enforcement)</li>
                <li>Complete audit logging of all agent operations</li>
                <li>Real-time monitoring through web dashboard</li>
                <li>Zero-trust security model with block-by-default enforcement</li>
            </ul>
        </div>
        
        <div class="feature">
            <h3>⚡ Technical Stack</h3>
            <ul>
                <li>Backend: Python 3.9+ with FastAPI + Streamlit</li>
                <li>Security: HMAC-SHA256 cryptographic verification</li>
                <li>Database: SQLite with WAL mode for audit trails</li>
                <li>Deployment: Docker, Vercel, Railway, GCP ready</li>
            </ul>
        </div>
    </body>
    </html>
    """)

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "argus", "version": "1.0.0"}

@app.get("/api/info")
async def api_info():
    """API information"""
    return {
        "name": "Argus Multi-Agent Governance System",
        "version": "1.0.0",
        "repository": "https://github.com/Adittyyaa/Argus_Agent",
        "description": "Cryptographic intent verification for AI agents",
        "features": [
            "Cryptographic delegation tokens",
            "Scoped agent authorization", 
            "Time-bounded access control",
            "Complete audit trail",
            "Interactive web GUI"
        ]
    }

def start_streamlit_dashboard():
    """Start Streamlit dashboard (for local development)"""
    if __name__ == '__main__':
        # Environment setup
        os.environ['PYTHONUNBUFFERED'] = '1'
        os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
        os.environ['STREAMLIT_SERVER_ENABLE_CORS'] = 'false'
        
        # Get port from environment
        port = os.environ.get('PORT', '8501')
        
        print(f"🚀 Starting Argus on port {port}")
        print("🌐 Multi-Agent Governance System")
        
        # Check if running in Vercel (has VERCEL env var)
        if os.environ.get('VERCEL'):
            print("📡 Running on Vercel - serving FastAPI endpoints")
            uvicorn.run(app, host="0.0.0.0", port=int(port))
        else:
            print("💻 Local development - starting Streamlit")
            # Streamlit command for local development
            cmd = [
                sys.executable, '-m', 'streamlit', 'run', 'dashboard/app.py',
                '--server.headless', 'true',
                '--server.port', port,
                '--server.address', '0.0.0.0',
                '--server.enableCORS', 'false',
                '--server.enableXsrfProtection', 'false',
                '--browser.gatherUsageStats', 'false'
            ]
            
            subprocess.run(cmd, check=True)

if __name__ == '__main__':
    start_streamlit_dashboard()