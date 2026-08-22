#!/bin/bash

# Argus Docker Deployment Script
# This script sets up and runs Argus using Docker Compose

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        echo "Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi
}

# Clean up existing containers and volumes
cleanup() {
    print_status "Cleaning up existing containers..."
    docker-compose down -v --remove-orphans 2>/dev/null || true
    docker system prune -f 2>/dev/null || true
}

# Build and start services
start_services() {
    print_status "Building Docker images..."
    docker-compose build --no-cache

    print_status "Starting services..."
    docker-compose up -d

    print_status "Waiting for services to be ready..."
    
    # Wait for services to be healthy
    max_attempts=30
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose ps | grep -q "Up (healthy)"; then
            break
        fi
        echo -n "."
        sleep 2
        ((attempt++))
    done
    echo ""
    
    if [ $attempt -eq $max_attempts ]; then
        print_warning "Services may not be fully ready yet. Check status with: docker-compose ps"
    fi
}

# Show service status
show_status() {
    print_status "Service Status:"
    docker-compose ps
    
    echo ""
    print_status "Service URLs:"
    echo "  Dashboard:     http://localhost:8501"
    echo "  Coordinator:   http://localhost:8000"
    echo "  Flight MCP:    http://localhost:8001"
    echo "  Calendar MCP:  http://localhost:8002"
    echo "  Shopping MCP:  http://localhost:8003"
}

# Run the demo
run_demo() {
    print_status "Running Argus demo..."
    docker-compose exec coordinator python coordinator/main.py
}

# Show logs
show_logs() {
    local service=${1:-""}
    if [ -n "$service" ]; then
        print_status "Showing logs for $service:"
        docker-compose logs -f "$service"
    else
        print_status "Showing logs for all services:"
        docker-compose logs -f
    fi
}

# Stop services
stop_services() {
    print_status "Stopping services..."
    docker-compose down
    print_success "Services stopped."
}

# Main menu
show_menu() {
    echo ""
    echo "=================================="
    echo "     Argus Docker Manager"
    echo "=================================="
    echo "1. Deploy (build and start all services)"
    echo "2. Show service status"
    echo "3. Run demo"
    echo "4. Show logs (all services)"
    echo "5. Show logs (specific service)"
    echo "6. Stop services"
    echo "7. Cleanup and redeploy"
    echo "8. Exit"
    echo "=================================="
}

# Main script logic
main() {
    print_status "Argus Docker Deployment Tool"
    
    # Check prerequisites
    check_docker
    
    # If arguments provided, run directly
    if [ $# -gt 0 ]; then
        case $1 in
            "start"|"deploy")
                start_services
                show_status
                ;;
            "stop")
                stop_services
                ;;
            "status")
                show_status
                ;;
            "logs")
                show_logs "$2"
                ;;
            "demo")
                run_demo
                ;;
            "cleanup")
                cleanup
                start_services
                show_status
                ;;
            *)
                echo "Usage: $0 [start|stop|status|logs|demo|cleanup]"
                exit 1
                ;;
        esac
        exit 0
    fi
    
    # Interactive menu
    while true; do
        show_menu
        read -p "Enter your choice [1-8]: " choice
        
        case $choice in
            1)
                start_services
                show_status
                ;;
            2)
                show_status
                ;;
            3)
                run_demo
                ;;
            4)
                show_logs
                ;;
            5)
                echo "Available services: coordinator, dashboard, flight-mcp, calendar-mcp, shopping-mcp"
                read -p "Enter service name: " service
                show_logs "$service"
                ;;
            6)
                stop_services
                ;;
            7)
                cleanup
                start_services
                show_status
                ;;
            8)
                print_status "Goodbye!"
                exit 0
                ;;
            *)
                print_error "Invalid choice. Please enter 1-8."
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
    done
}

# Run main function with all arguments
main "$@"