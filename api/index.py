"""
Vercel-compatible wrapper for Argus Streamlit app
"""

import os
import sys
import subprocess
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def start_streamlit():
    """Start Streamlit in background"""
    os.environ['PYTHONUNBUFFERED'] = '1'
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 
        '../dashboard/app.py',
        '--server.headless', 'true',
        '--server.port', '8501',
        '--server.address', '0.0.0.0',
        '--server.enableCORS', 'false'
    ]
    
    subprocess.Popen(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))

# Start Streamlit when module loads
start_streamlit()
time.sleep(2)  # Give Streamlit time to start

def handler(environ, start_response):
    """WSGI handler that proxies to Streamlit"""
    import requests
    
    try:
        # Proxy request to Streamlit
        streamlit_url = f"http://localhost:8501{environ.get('PATH_INFO', '')}"
        
        if environ.get('QUERY_STRING'):
            streamlit_url += f"?{environ['QUERY_STRING']}"
        
        response = requests.get(streamlit_url, timeout=10)
        
        status = f"{response.status_code} {response.reason}"
        headers = [('Content-Type', 'text/html')]
        
        start_response(status, headers)
        return [response.content]
        
    except Exception as e:
        # Fallback response
        status = '200 OK'
        headers = [('Content-Type', 'text/html')]
        start_response(status, headers)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Argus - Multi-Agent Governance System</title>
            <meta http-equiv="refresh" content="3">
        </head>
        <body>
            <h1>🚀 Argus is Starting...</h1>
            <p>Multi-Agent Governance System is initializing.</p>
            <p>This page will refresh automatically.</p>
            <p><strong>Repository:</strong> <a href="https://github.com/Adittyyaa/Argus_Agent">https://github.com/Adittyyaa/Argus_Agent</a></p>
            <p><em>Error: {str(e)}</em></p>
        </body>
        </html>
        """
        return [html.encode()]

# For Vercel
app = handler