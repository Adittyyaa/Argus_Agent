# Argus Docker Deployment Guide

## Quick Start (Option 1: Docker Compose)

### Prerequisites
- Docker Desktop installed on your machine
- Git (to share/clone the repository)

### 1. Deploy Locally

```bash
# Navigate to the project directory
cd argus

# Run the deployment script
./docker-deploy.sh

# Or manually with docker-compose
docker-compose up -d --build
```

### 2. Access the Application

Once deployed, you can access:

- **Dashboard**: http://localhost:8501 (Streamlit audit dashboard)
- **Coordinator**: http://localhost:8000 (Main service)
- **MCP Servers**: 
  - Flight: http://localhost:8001
  - Calendar: http://localhost:8002  
  - Shopping: http://localhost:8003

### 3. Run the Demo

```bash
# Using the deployment script
./docker-deploy.sh demo

# Or directly
docker-compose exec coordinator python coordinator/main.py
```

### 4. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f coordinator
docker-compose logs -f dashboard
```

### 5. Stop Services

```bash
docker-compose down
```

## How to Share Your Deployment

### Method 1: GitHub Repository

1. **Create a GitHub repository:**
```bash
cd argus
git init
git add .
git commit -m "Initial Argus deployment"
git remote add origin https://github.com/yourusername/argus.git
git push -u origin main
```

2. **Share with others:**
```bash
# Others can clone and run
git clone https://github.com/yourusername/argus.git
cd argus
./docker-deploy.sh
```

### Method 2: Docker Hub (Share Pre-built Images)

1. **Build and push images:**
```bash
# Build the image
docker build -t yourusername/argus:latest .

# Push to Docker Hub
docker push yourusername/argus:latest
```

2. **Update docker-compose.yml to use your image:**
```yaml
services:
  coordinator:
    image: yourusername/argus:latest
    # ... rest of config
```

### Method 3: Cloud Deployment (Easiest Sharing)

#### Railway (Recommended for sharing)

1. **Install Railway CLI:**
```bash
npm install -g @railway/cli
```

2. **Deploy:**
```bash
railway login
railway init
railway up
```

3. **Share the URL:** Railway gives you a public URL like `https://argus-production.railway.app`

#### DigitalOcean App Platform

1. **Create account on DigitalOcean**
2. **Go to Apps section**
3. **Connect your GitHub repository**
4. **Deploy with one click**

### Method 4: Local Network Sharing

To share on your local network (same WiFi):

1. **Find your IP address:**
```bash
# macOS/Linux
ifconfig | grep "inet " | grep -v 127.0.0.1

# Windows
ipconfig | findstr "IPv4"
```

2. **Update docker-compose.yml ports to bind to all interfaces:**
```yaml
ports:
  - "0.0.0.0:8501:8501"  # Dashboard
  - "0.0.0.0:8000:8000"  # Coordinator
```

3. **Others on same network can access:**
   - Dashboard: http://YOUR_IP:8501
   - Example: http://192.168.1.100:8501

## Demo Script for Sharing

Create `demo.sh` for easy demonstrations:

```bash
#!/bin/bash
echo "🚀 Starting Argus Demo..."

# Start services
./docker-deploy.sh start

echo "⏳ Waiting for services to be ready..."
sleep 10

echo "🎯 Running the governance demo..."
docker-compose exec -T coordinator python coordinator/main.py

echo "📊 Demo complete! Visit the dashboard:"
echo "   http://localhost:8501"
echo ""
echo "Press any key to stop services..."
read -n 1
docker-compose down
```

## Sharing Package

To create a complete sharing package:

```bash
# Create a zip file with everything needed
zip -r authorchain-demo.zip \
  *.py \
  agents/ \
  audit/ \
  coordinator/ \
  dashboard/ \
  mcp_servers/ \
  mock_armoriq/ \
  tests/ \
  requirements.txt \
  Dockerfile \
  docker-compose.yml \
  docker-deploy.sh \
  DOCKER_DEPLOYMENT.md \
  README.md
```

Send this zip file to anyone, and they can:
1. Extract it
2. Run `./docker-deploy.sh`
3. Access the dashboard at http://localhost:8501

## Troubleshooting

### Port Conflicts
```bash
# Kill processes using the ports
lsof -ti:8000,8001,8002,8003,8501 | xargs kill -9

# Or use different ports in docker-compose.yml
ports:
  - "9501:8501"  # Use port 9501 instead of 8501
```

### Permission Issues
```bash
# Make script executable
chmod +x docker-deploy.sh

# Fix Docker permissions (Linux)
sudo usermod -aG docker $USER
```

### Memory Issues
```bash
# Increase Docker memory limit in Docker Desktop settings
# Or reduce container resources in docker-compose.yml
```

### Service Not Starting
```bash
# Check logs
docker-compose logs coordinator

# Restart specific service
docker-compose restart coordinator
```

## Production Deployment Notes

For production deployment, update:

1. **Environment variables:**
```yaml
environment:
  - ARMORIQ_MODE=real
  - ARMORIQ_API_KEY=your-real-api-key
  - DATABASE_URL=postgresql://user:pass@host:5432/authorchain
```

2. **Use external database:**
```yaml
# Remove sqlite, add PostgreSQL service or external DB
services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: authorchain
      POSTGRES_USER: authorchain
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

3. **Add reverse proxy:**
```yaml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf
```

This setup provides a complete, shareable deployment that anyone can run with minimal setup.