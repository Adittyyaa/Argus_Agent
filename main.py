#!/usr/bin/env python3
"""
main.py - Argus Multi-Agent Governance System
Entry point for Zop cloud deployment.
"""

import os
import sys
import subprocess

def main():
    # Zop injects $PORT — fall back to 8501 for local dev
    port = os.environ.get('PORT', '8501')

    print(f"[Argus] Starting on port {port}")

    cmd = [
        sys.executable, '-m', 'streamlit', 'run',
        'dashboard/app.py',
        '--server.port', port,
        '--server.address', '0.0.0.0',
        '--server.headless', 'true',
        '--server.enableCORS', 'false',
        '--server.enableXsrfProtection', 'false',
        '--browser.gatherUsageStats', 'false',
    ]

    os.execvp(sys.executable, cmd)  # replace process (no subprocess, no zombie)

if __name__ == '__main__':
    main()
