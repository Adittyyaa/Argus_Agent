#!/bin/bash

# Argus Cloud Deployment Script
# Handles SSL/TLS configuration for cloud deployment

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Create cloud-ready docker-compose file
create_cloud_compose() {
    print_status "Creating cloud deployment configuration..."
    
    cat > docker-compose.cloud.yml << 'EOF'
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - dashboard
      - coordinator
    restart: unless-stopped

  coordinator:
    build: .
    command: python coordinator/main.py
    environment:
      - PYTHONUNBUFFERED=1
      - ARMORIQ_MODE=mock
    volumes:
      - ./data:/app/data
    expose:
      - "8000"
    restart: unless-stopped

  dashboard:
    build: .
    command: streamlit run dashboard/app.py --server.headless true --server.port 8501 --server.address 0.0.0.0
    environment:
      - PYTHONUNBUFFERED=1
    expose:
      - "8501"
    restart: unless-stopped

  flight-mcp:
    build: .
    command: python mcp_servers/flight_mcp.py
    environment:
      - PYTHONUNBUFFERED=1
    expose:
      - "8001"
    restart: unless-stopped

  calendar-mcp:
    build: .
    command: python mcp_servers/calendar_mcp.py
    environment:
      - PYTHONUNBUFFERED=1
    expose:
      - "8002"
    restart: unless-stopped

  shopping-mcp:
    build: .
    command: python mcp_servers/shopping_mcp.py
    environment:
      - PYTHONUNBUFFERED=1
    expose:
      - "8003"
    restart: unless-stopped

volumes:
  data:

networks:
  default:
    name: argus-network
EOF

    print_success "Cloud docker-compose.yml created"
}

# Create Nginx configuration for SSL/TLS
create_nginx_config() {
    print_status "Creating Nginx configuration for SSL/TLS..."
    
    cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream dashboard {
        server dashboard:8501;
    }
    
    upstream coordinator {
        server coordinator:8000;
    }

    # HTTP to HTTPS redirect
    server {
        listen 80;
        server_name _;
        return 301 https://$host$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name _;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        
        # Strong SSL configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_prefer_server_ciphers off;
        ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

        # Dashboard (main interface)
        location / {
            proxy_pass http://dashboard;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support for Streamlit
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_read_timeout 86400;
        }

        # API endpoints
        location /api/ {
            proxy_pass http://coordinator/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
EOF

    print_success "Nginx configuration created"
}

# Generate self-signed SSL certificates (for development/testing)
generate_ssl_certs() {
    print_status "Generating SSL certificates..."
    
    mkdir -p ssl
    
    # Generate private key
    openssl genrsa -out ssl/key.pem 2048
    
    # Generate certificate signing request
    openssl req -new -key ssl/key.pem -out ssl/cert.csr -subj "/C=US/ST=CA/L=San Francisco/O=Argus/OU=Demo/CN=*.zopcloud.zop.dev"
    
    # Generate self-signed certificate
    openssl x509 -req -days 365 -in ssl/cert.csr -signkey ssl/key.pem -out ssl/cert.pem
    
    # Clean up CSR
    rm ssl/cert.csr
    
    print_success "SSL certificates generated in ssl/ directory"
    print_warning "These are self-signed certificates for development only"
}

# Create production-ready Dockerfile
create_production_dockerfile() {
    print_status "Creating production Dockerfile..."
    
    cat > Dockerfile.prod << 'EOF'
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Create data directory
RUN mkdir -p /app/data

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8501/health', timeout=5)" || exit 1

EXPOSE 8501 8000 8001 8002 8003

CMD ["streamlit", "run", "dashboard/app.py", "--server.headless", "true", "--server.port", "8501", "--server.address", "0.0.0.0"]
EOF

    print_success "Production Dockerfile created"
}

# Create deployment script for cloud platforms
create_deploy_script() {
    print_status "Creating cloud deployment script..."
    
    cat > deploy-to-cloud.sh << 'EOF'
#!/bin/bash

# Cloud Platform Deployment Script

set -e

PLATFORM=${1:-"generic"}
DOMAIN=${2:-"argus.zopcloud.zop.dev"}

echo "Deploying Argus to $PLATFORM with domain $DOMAIN"

case $PLATFORM in
    "railway")
        echo "Deploying to Railway..."
        railway up
        ;;
    "heroku")
        echo "Deploying to Heroku..."
        heroku container:push web
        heroku container:release web
        ;;
    "digitalocean")
        echo "Deploying to DigitalOcean App Platform..."
        doctl apps create --spec app.yaml
        ;;
    "vercel")
        echo "Deploying to Vercel..."
        vercel --prod
        ;;
    *)
        echo "Generic cloud deployment..."
        docker-compose -f docker-compose.cloud.yml up --build -d
        ;;
esac

echo "Deployment complete!"
echo "Access your app at: https://$DOMAIN"
EOF

    chmod +x deploy-to-cloud.sh
    print_success "Cloud deployment script created"
}

# Fix Streamlit for cloud deployment
fix_streamlit_config() {
    print_status "Creating Streamlit cloud configuration..."
    
    mkdir -p .streamlit
    
    cat > .streamlit/config.toml << 'EOF'
[server]
headless = true
port = 8501
address = "0.0.0.0"
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#6366f1"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f8fafc"
textColor = "#1f2937"
EOF

    print_success "Streamlit configuration created"
}

# Create app.yaml for cloud platforms
create_app_yaml() {
    print_status "Creating app.yaml for cloud platforms..."
    
    cat > app.yaml << 'EOF'
name: argus
services:
- name: web
  source_dir: .
  github:
    repo: your-username/hackathon
    branch: main
  run_command: streamlit run dashboard/app.py --server.headless true --server.port $PORT --server.address 0.0.0.0
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: PORT
    value: "8501"
  - key: PYTHONUNBUFFERED
    value: "1"
  - key: ARMORIQ_MODE
    value: "mock"
EOF

    print_success "app.yaml created for DigitalOcean App Platform"
}

# Create Procfile for Heroku
create_procfile() {
    print_status "Creating Procfile for Heroku..."
    
    cat > Procfile << 'EOF'
web: streamlit run dashboard/app.py --server.headless true --server.port $PORT --server.address 0.0.0.0
EOF

    print_success "Procfile created for Heroku deployment"
}

# Main deployment function
deploy_to_cloud() {
    print_status "Setting up Argus for cloud deployment..."
    
    # Create all necessary files
    create_cloud_compose
    create_nginx_config
    generate_ssl_certs
    create_production_dockerfile
    fix_streamlit_config
    create_app_yaml
    create_procfile
    create_deploy_script
    
    print_success "Cloud deployment setup complete!"
    
    echo ""
    echo "=============================================="
    echo "           DEPLOYMENT INSTRUCTIONS"
    echo "=============================================="
    echo ""
    echo "1. For HTTPS/SSL deployment:"
    echo "   docker-compose -f docker-compose.cloud.yml up --build -d"
    echo ""
    echo "2. For specific cloud platforms:"
    echo "   ./deploy-to-cloud.sh railway"
    echo "   ./deploy-to-cloud.sh heroku"
    echo "   ./deploy-to-cloud.sh digitalocean"
    echo ""
    echo "3. Access your app at:"
    echo "   https://your-domain.com"
    echo ""
    echo "4. For custom SSL certificates:"
    echo "   - Replace files in ssl/ directory with your certificates"
    echo "   - cert.pem (certificate)"
    echo "   - key.pem (private key)"
    echo ""
    echo "=============================================="
}

# Main script
case ${1:-"setup"} in
    "setup"|"")
        deploy_to_cloud
        ;;
    "ssl")
        generate_ssl_certs
        ;;
    "nginx")
        create_nginx_config
        ;;
    "deploy")
        print_status "Starting cloud deployment..."
        docker-compose -f docker-compose.cloud.yml up --build -d
        print_success "Cloud deployment started!"
        ;;
    *)
        echo "Usage: $0 [setup|ssl|nginx|deploy]"
        exit 1
        ;;
esac