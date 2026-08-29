#!/bin/bash

# Google Cloud Platform Deployment Fix Script
# Fixes IAP tunnel and firewall issues

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

# Check if gcloud is installed and authenticated
check_gcloud() {
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI not found. Please install Google Cloud SDK first:"
        echo "  curl https://sdk.cloud.google.com | bash"
        echo "  exec -l \$SHELL"
        exit 1
    fi
    
    # Check if authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
        print_warning "Not authenticated with gcloud. Running authentication..."
        gcloud auth login
    fi
    
    print_success "gcloud CLI is ready"
}

# Set project and get project info
setup_project() {
    print_status "Setting up GCP project..."
    
    # List available projects
    echo "Available projects:"
    gcloud projects list --format="table(projectId,name,projectNumber)"
    
    read -p "Enter your project ID: " PROJECT_ID
    
    if [ -z "$PROJECT_ID" ]; then
        print_error "Project ID cannot be empty"
        exit 1
    fi
    
    gcloud config set project $PROJECT_ID
    print_success "Project set to: $PROJECT_ID"
    
    export PROJECT_ID
}

# Fix firewall rules for IAP
fix_firewall() {
    print_status "Fixing firewall rules for IAP tunnel..."
    
    # Create firewall rule for IAP access
    print_status "Creating firewall rule for IAP SSH access..."
    gcloud compute firewall-rules create allow-iap-ssh \
        --direction=INGRESS \
        --priority=1000 \
        --network=default \
        --action=ALLOW \
        --rules=tcp:22 \
        --source-ranges=35.235.240.0/20 \
        --target-tags=iap-ssh || print_warning "Firewall rule may already exist"
    
    # Create firewall rule for web traffic
    print_status "Creating firewall rule for web traffic..."
    gcloud compute firewall-rules create allow-argus-web \
        --direction=INGRESS \
        --priority=1000 \
        --network=default \
        --action=ALLOW \
        --rules=tcp:8501,tcp:8000,tcp:80,tcp:443 \
        --source-ranges=0.0.0.0/0 \
        --target-tags=argus-web || print_warning "Web firewall rule may already exist"
    
    print_success "Firewall rules configured"
}

# Fix IAP permissions
fix_iap_permissions() {
    print_status "Fixing IAP permissions..."
    
    # Get current user email
    USER_EMAIL=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
    
    # Get project number
    PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
    
    # Get compute engine default service account
    COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
    
    # Get Cloud Build service account and agent
    CLOUDBUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"
    CLOUDBUILD_SA_AGENT="service-${PROJECT_NUMBER}@gcp-sa-cloudbuild.iam.gserviceaccount.com"
    
    print_status "Granting IAP tunnel access to Compute Engine service account..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:${COMPUTE_SA}" \
        --role="roles/iap.tunnelResourceAccessor"
    
    print_status "Granting IAP tunnel access to Cloud Build service account..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:${CLOUDBUILD_SA}" \
        --role="roles/iap.tunnelResourceAccessor" || print_warning "Could not grant IAP tunnel access to Cloud Build service account"
        
    print_status "Granting IAP tunnel access to Cloud Build service agent..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:${CLOUDBUILD_SA_AGENT}" \
        --role="roles/iap.tunnelResourceAccessor" || print_warning "Could not grant IAP tunnel access to Cloud Build service agent"
    
    print_status "Granting IAP tunnel access to user..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="user:${USER_EMAIL}" \
        --role="roles/iap.tunnelResourceAccessor"
    
    print_success "IAP permissions configured"
}

# Enable required APIs
enable_apis() {
    print_status "Enabling required Google Cloud APIs..."
    
    gcloud services enable compute.googleapis.com
    gcloud services enable iap.googleapis.com
    gcloud services enable cloudbuild.googleapis.com
    gcloud services enable run.googleapis.com
    
    print_success "Required APIs enabled"
}

# Create VM instance for deployment
create_vm() {
    print_status "Creating VM instance for Argus deployment..."
    
    VM_NAME="argus-vm"
    ZONE="us-central1-a"
    
    # Check if VM already exists
    if gcloud compute instances describe $VM_NAME --zone=$ZONE &>/dev/null; then
        print_warning "VM $VM_NAME already exists"
        return
    fi
    
    # Create VM with appropriate tags and configuration
    gcloud compute instances create $VM_NAME \
        --zone=$ZONE \
        --machine-type=e2-medium \
        --network-interface=network-tier=PREMIUM,subnet=default \
        --maintenance-policy=MIGRATE \
        --provisioning-model=STANDARD \
        --tags=iap-ssh,argus-web,http-server,https-server \
        --create-disk=auto-delete=yes,boot=yes,device-name=$VM_NAME,image=projects/ubuntu-os-cloud/global/images/ubuntu-2004-focal-v20231101,mode=rw,size=20,type=projects/$PROJECT_ID/zones/$ZONE/diskTypes/pd-balanced \
        --no-shielded-secure-boot \
        --shielded-vtpm \
        --shielded-integrity-monitoring \
        --labels=environment=development,app=argus \
        --reservation-affinity=any
    
    print_success "VM instance created: $VM_NAME"
}

# Deploy using Cloud Run (Alternative method)
deploy_cloud_run() {
    print_status "Alternative: Deploying to Cloud Run..."
    
    # Build and deploy to Cloud Run
    gcloud run deploy argus \
        --source . \
        --platform managed \
        --region us-central1 \
        --allow-unauthenticated \
        --port 8501 \
        --set-env-vars="PYTHONUNBUFFERED=1,ARMORIQ_MODE=mock" \
        --memory=1Gi \
        --cpu=1 \
        --max-instances=10
    
    print_success "Deployed to Cloud Run"
    
    # Get the service URL
    SERVICE_URL=$(gcloud run services describe argus --region=us-central1 --format="value(status.url)")
    print_success "Service available at: $SERVICE_URL"
}

# Test IAP connection
test_connection() {
    print_status "Testing IAP connection..."
    
    VM_NAME="argus-vm"
    ZONE="us-central1-a"
    
    # Test connection
    if gcloud compute ssh $VM_NAME --zone=$ZONE --tunnel-through-iap --dry-run; then
        print_success "IAP tunnel connection test passed"
    else
        print_error "IAP tunnel test failed"
        print_status "Trying alternative deployment method..."
        deploy_cloud_run
    fi
}

# Main menu
show_menu() {
    echo ""
    echo "=================================="
    echo "   GCP Deployment Fix Menu"
    echo "=================================="
    echo "1. Full fix (recommended)"
    echo "2. Fix firewall rules only"
    echo "3. Fix IAP permissions only" 
    echo "4. Deploy to Cloud Run (alternative)"
    echo "5. Create VM instance"
    echo "6. Test connection"
    echo "7. Exit"
    echo "=================================="
}

# Main function
main() {
    print_status "Google Cloud Platform Deployment Fix"
    
    check_gcloud
    
    if [ $# -eq 0 ]; then
        # Interactive mode
        setup_project
        
        while true; do
            show_menu
            read -p "Choose an option [1-7]: " choice
            
            case $choice in
                1)
                    enable_apis
                    fix_firewall
                    fix_iap_permissions
                    create_vm
                    test_connection
                    ;;
                2)
                    fix_firewall
                    ;;
                3)
                    fix_iap_permissions
                    ;;
                4)
                    deploy_cloud_run
                    ;;
                5)
                    create_vm
                    ;;
                6)
                    test_connection
                    ;;
                7)
                    print_status "Goodbye!"
                    exit 0
                    ;;
                *)
                    print_error "Invalid choice"
                    ;;
            esac
            
            echo ""
            read -p "Press Enter to continue..."
        done
    else
        # Command line mode
        case $1 in
            "fix-all")
                setup_project
                enable_apis
                fix_firewall
                fix_iap_permissions
                create_vm
                test_connection
                ;;
            "cloud-run")
                setup_project
                deploy_cloud_run
                ;;
            *)
                echo "Usage: $0 [fix-all|cloud-run]"
                exit 1
                ;;
        esac
    fi
}

main "$@"