#!/usr/bin/env python3
"""
main.py
=======
Alternative entry point for Zop platform deployment.
Fixes 502 Bad Gateway errors by ensuring proper port binding.
"""

import os
import sys
import subprocess

def main():
    """Start Streamlit with cloud-optimized settings"""
    
    # Environment setup
    os.environ['PYTHONUNBUFFERED'] = '1'
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    os.environ['STREAMLIT_SERVER_ENABLE_CORS'] = 'false'
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    
    # Get port from environment
    port = os.environ.get('PORT', '8501')
    
    print(f"🚀 Starting Argus on port {port}")
    print("🌐 Platform: Zop Cloud")
    print("📍 URL: https://argus.zopcloud.zop.dev")
    
    # Streamlit command with all necessary flags
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 'dashboard/app.py',
        '--server.headless', 'true',
        '--server.port', port,
        '--server.address', '0.0.0.0',
        '--server.enableCORS', 'false',
        '--server.enableXsrfProtection', 'false',
        '--browser.gatherUsageStats', 'false',
        '--server.baseUrlPath', '',
        '--runner.magicEnabled', 'false'
    ]
    
    print(f"📋 Command: {' '.join(cmd)}")
    
    try:
        # Execute Streamlit
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting Streamlit: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("🛑 Shutdown requested")
        sys.exit(0)

if __name__ == '__main__':
    main()