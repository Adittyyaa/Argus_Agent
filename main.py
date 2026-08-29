#!/usr/bin/env python3
"""
main.py - Argus Multi-Agent Governance System
Entry point for Zop cloud deployment.
"""

import os
import sys
import subprocess

def main():
    port = os.environ.get('PORT', '8501')

    os.environ['PYTHONUNBUFFERED'] = '1'
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    os.environ['STREAMLIT_SERVER_ENABLE_CORS'] = 'false'
    os.environ['STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION'] = 'false'
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'

    print(f"Starting Argus on port {port}")

    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 'dashboard/app.py',
        '--server.headless', 'true',
        '--server.port', port,
        '--server.address', '0.0.0.0',
        '--server.enableCORS', 'false',
        '--server.enableXsrfProtection', 'false',
        '--browser.gatherUsageStats', 'false',
    ]

    subprocess.run(cmd, check=True)

if __name__ == '__main__':
    main()
