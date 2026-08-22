#!/bin/bash

# Argus Deployment Verification Script
# Run this after extracting the zip to verify everything works

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[CHECK]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

echo "======================================="
echo "🔍 Argus Deployment Verification"
echo "======================================="

# Check Docker
print_status "Checking Docker installation..."
if command -v docker >/dev/null 2>&1; then
    DOCKER_VERSION=$(docker --version)
    print_success "Docker found: $DOCKER_VERSION"
else
    print_error "Docker not installed. Please run: brew install --cask docker"
    echo "Or see INSTALL_DOCKER.md for detailed instructions"
    exit 1
fi

# Check Docker Compose
print_status "Checking Docker Compose..."
if docker-compose --version >/dev/null 2>&1 || docker compose version >/dev/null 2>&1; then
    print_success "Docker Compose is available"
else
    print_error "Docker Compose not available"
    exit 1
fi

# Check Docker is running
print_status "Checking if Docker daemon is running..."
if docker info >/dev/null 2>&1; then
    print_success "Docker daemon is running"
else
    print_error "Docker daemon not running. Please start Docker Desktop"
    echo "Run: open -a Docker"
    exit 1
fi

# Check file permissions
print_status "Checking script permissions..."
if [ -x "docker-deploy.sh" ]; then
    print_success "docker-deploy.sh is executable"
else
    print_warning "Making docker-deploy.sh executable..."
    chmod +x docker-deploy.sh
    print_success "Fixed permissions"
fi

if [ -x "run_demo.sh" ]; then
    print_success "run_demo.sh is executable"
else
    print_warning "Making run_demo.sh executable..."
    chmod +x run_demo.sh
    print_success "Fixed permissions"
fi

# Check required files
print_status "Checking required files..."
REQUIRED_FILES=(
    "docker-compose.yml"
    "Dockerfile"
    "requirements.txt"
    "coordinator/main.py"
    "dashboard/app.py"
    "mcp_servers/flight_mcp.py"
    "mcp_servers/calendar_mcp.py"
    "mcp_servers/shopping_mcp.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_success "Found $file"
    else
        print_error "Missing $file"
        exit 1
    fi
done

# Check ports
print_status "Checking for port conflicts..."
PORTS=(8000 8001 8002 8003 8501)
CONFLICTS=0

for port in "${PORTS[@]}"; do
    if lsof -i:$port >/dev/null 2>&1; then
        print_warning "Port $port is in use"
        CONFLICTS=1
    else
        print_success "Port $port is available"
    fi
done

if [ $CONFLICTS -eq 1 ]; then
    print_warning "Some ports are in use. Run this to free them:"
    echo "lsof -ti:8000,8001,8002,8003,8501 | xargs kill -9"
fi

echo ""
echo "======================================="
print_success "✅ Verification Complete!"
echo "======================================="
echo ""
echo "🚀 Ready to deploy! Run these commands:"
echo ""
echo "1. Deploy the system:"
echo "   ./docker-deploy.sh start"
echo ""
echo "2. Run the demo:"
echo "   ./docker-deploy.sh demo"
echo ""
echo "3. View the dashboard:"
echo "   open http://localhost:8501"
echo ""
echo "For help: ./docker-deploy.sh (interactive menu)"
echo ""