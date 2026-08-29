# Fix SSL Deployment Error

## Problem
Getting `ERR_SSL_PROTOCOL_ERROR` when deploying to `argus.zopcloud.zop.dev`

## Immediate Solutions

### 1. Quick Fix - Use HTTP (Development Only)
```bash
# Try accessing via HTTP instead of HTTPS
http://argus.zopcloud.zop.dev
```

### 2. Local Testing
```bash
# Test locally first
streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0
# Then access via: http://localhost:8501
```

### 3. Cloud Deployment with SSL Fix
```bash
# Run the cloud deployment script
./cloud-deploy.sh setup

# This creates:
# - SSL-ready nginx configuration  
# - Self-signed certificates
# - Cloud-ready Docker setup
# - Fixed Streamlit configuration
```

### 4. Platform-Specific Deployment

#### For Railway:
```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway init
railway up
```

#### For Vercel:
```bash
# Install Vercel CLI  
npm install -g vercel

# Deploy
vercel --prod
```

#### For Heroku:
```bash
# Install Heroku CLI and deploy
heroku create argus-demo
git push heroku main
```

## Root Cause
The SSL error occurs because:
1. Cloud platform expects HTTPS but app serves HTTP
2. Missing SSL certificates  
3. Incorrect Streamlit configuration for cloud deployment
4. CORS/WebSocket configuration issues

## Fixed Files
- `dashboard/app.py` - Added SSL context fix
- `.streamlit/config.toml` - Cloud-ready Streamlit config
- `cloud-deploy.sh` - Complete cloud deployment setup
- `docker-compose.cloud.yml` - SSL-ready Docker configuration

## Test Locally First
```bash
# 1. Start local server
streamlit run dashboard/app.py

# 2. Verify it works at http://localhost:8501

# 3. Then deploy to cloud with proper SSL configuration
```

## Production Deployment
For production, replace self-signed certificates in `ssl/` directory with:
- `cert.pem` - Your SSL certificate
- `key.pem` - Your private key

## Support
If issues persist, try:
1. Different cloud platform (Railway, Vercel, Heroku)
2. Local deployment first to verify functionality
3. Check cloud platform specific SSL requirements