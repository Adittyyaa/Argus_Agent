# Zop Platform Deployment Guide for Argus

## 🚀 Quick Deployment Steps

### 1. Repository Information
- **Repository**: https://github.com/Adittyyaa/Argus_Agent
- **Branch**: main
- **Framework**: Streamlit (Python)

### 2. Zop Platform Configuration

#### Build Settings:
```bash
# Build Command:
pip install -r requirements.txt

# Start Command:
streamlit run dashboard/app.py --server.headless true --server.port $PORT --server.address 0.0.0.0 --server.enableCORS false
```

#### Environment Variables:
```
PORT=8501
PYTHONUNBUFFERED=1
ARMORIQ_MODE=mock
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_ENABLE_CORS=false
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

#### Runtime:
- **Language**: Python 3.9+
- **Port**: 8501 (or $PORT from environment)
- **Health Check**: GET / (returns 200)

### 3. Deployment Files Ready
- ✅ `Procfile` - Process configuration
- ✅ `requirements.txt` - Python dependencies  
- ✅ `start.sh` - Startup script
- ✅ `zop.json` - Zop-specific configuration
- ✅ `.streamlit/config.toml` - Streamlit cloud settings

### 4. Expected Result
- **URL**: https://argus.zopcloud.zop.dev
- **Features**: Full Argus GUI with custom agent control
- **Security**: SSL/HTTPS enabled automatically

## 🔧 Troubleshooting

### If SSL Protocol Error Persists:
1. Check that CORS is disabled in environment variables
2. Verify PORT environment variable is set correctly
3. Ensure health check endpoint responds

### Alternative Start Commands:
```bash
# Option 1 (current):
streamlit run dashboard/app.py --server.headless true --server.port $PORT --server.address 0.0.0.0 --server.enableCORS false

# Option 2 (if issues):
python -m streamlit run dashboard/app.py --server.headless true --server.port $PORT --server.address 0.0.0.0

# Option 3 (minimal):
streamlit run dashboard/app.py --server.port $PORT
```

### Files to Reference:
- Main app: `dashboard/app.py`
- Configuration: `.streamlit/config.toml`
- Dependencies: `requirements.txt`
- Start script: `start.sh` or `Procfile`

## 📱 Deployment Steps on Zop

1. **Connect Repository**: https://github.com/Adittyyaa/Argus_Agent
2. **Set Build Command**: `pip install -r requirements.txt`
3. **Set Start Command**: Use command from Procfile or start.sh
4. **Add Environment Variables**: PORT, PYTHONUNBUFFERED, ARMORIQ_MODE
5. **Deploy**: Should be live at argus.zopcloud.zop.dev

## ✅ Verification

Once deployed:
- Visit: https://argus.zopcloud.zop.dev
- Should see: Argus Control Center & Audit Dashboard
- Test: Go to "Custom Agent Control" tab
- Verify: No SSL protocol errors

The deployment should now work properly with the SSL fixes we implemented!