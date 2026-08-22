# Docker Installation Guide for macOS

## Method 1: Docker Desktop (Recommended)

### For Apple Silicon Macs (M1/M2/M3/M4)
```bash
# Download and install via Homebrew
brew install --cask docker

# Or download directly
curl -L https://desktop.docker.com/mac/main/arm64/Docker.dmg -o Docker.dmg
```

### For Intel Macs
```bash
# Download and install via Homebrew  
brew install --cask docker

# Or download directly
curl -L https://desktop.docker.com/mac/main/amd64/Docker.dmg -o Docker.dmg
```

### Manual Installation
1. Download Docker Desktop from: https://www.docker.com/products/docker-desktop
2. Double-click the `.dmg` file
3. Drag Docker to Applications folder
4. Launch Docker from Applications
5. Follow the setup wizard

## Method 2: Command Line Only (Advanced)

```bash
# Install Docker Engine via Homebrew
brew install docker docker-compose

# Note: You'll need to set up Docker daemon separately
```

## Start Docker Desktop

```bash
# Start Docker Desktop application
open -a Docker

# Wait for Docker to start (whale icon appears in menu bar)
```

## Verify Installation

```bash
# Check Docker version
docker --version

# Check Docker Compose version  
docker-compose --version

# Test Docker is working
docker run hello-world
```

Expected output:
```
Hello from Docker!
This message shows that your installation appears to be working correctly.
```

## Post-Installation

### Enable Docker at Startup (Optional)
1. Open Docker Desktop preferences
2. Go to General tab
3. Check "Start Docker Desktop when you log in"

### Increase Resources (Optional)
1. Open Docker Desktop preferences
2. Go to Resources tab
3. Increase Memory to 4GB+ for better performance
4. Increase CPU cores if available

## Troubleshooting

### Docker Desktop Won't Start
```bash
# Kill existing Docker processes
pkill -f docker

# Restart Docker Desktop
open -a Docker
```

### Permission Issues
```bash
# Add user to docker group (on Linux-like systems)
sudo usermod -aG docker $USER

# Restart terminal or log out/in
```

### Port Conflicts
```bash
# Check what's using ports
lsof -i :8000,8001,8002,8003,8501

# Kill processes if needed
lsof -ti:8000,8001,8002,8003,8501 | xargs kill -9
```

## Alternative: Colima (Lightweight)

If you prefer a lighter alternative to Docker Desktop:

```bash
# Install Colima
brew install colima docker docker-compose

# Start Colima
colima start

# Verify
docker --version
```

## Ready to Deploy Argus

Once Docker is installed and running:

```bash
cd argus
./docker-deploy.sh start
```

You should see all services starting up successfully!