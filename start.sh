#!/bin/bash
# Zop Platform Startup Script - Fixed for 502 errors

set -e

# Environment setup
export PYTHONUNBUFFERED=1
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_SERVER_ENABLE_CORS=false
export STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Use PORT from environment or default to 8501
PORT=${PORT:-8501}

echo "🚀 Starting Argus on port $PORT..."
echo "🌐 Environment: Zop Platform"
echo "📍 Expected URL: https://argus.zopcloud.zop.dev"

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Check if required files exist
if [ ! -f "dashboard/app.py" ]; then
    echo "❌ Error: dashboard/app.py not found"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found" 
    exit 1
fi

echo "✅ Files verified, starting Streamlit..."

# Start Streamlit with comprehensive cloud settings
exec python3 -m streamlit run dashboard/app.py \
  --server.headless true \
  --server.port $PORT \
  --server.address 0.0.0.0 \
  --server.enableCORS false \
  --server.enableXsrfProtection false \
  --browser.gatherUsageStats false \
  --server.baseUrlPath "" \
  --server.enableWebsocketCompression false \
  --runner.magicEnabled false \
  --server.allowRunOnSave false