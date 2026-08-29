#!/bin/bash
# Zop Platform Startup Script

set -e
export PYTHONUNBUFFERED=1
PORT=${PORT:-8501}

echo "Starting Argus on port $PORT..."
streamlit run dashboard/app.py --server.headless true --server.port $PORT --server.address 0.0.0.0 --server.enableCORS false