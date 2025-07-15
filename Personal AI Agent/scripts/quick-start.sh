#!/bin/bash

# Personal AI Agent - Quick Start Setup Script
# This script sets up the entire monorepo for hybrid deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project information
PROJECT_NAME="Personal AI Agent"
VERSION="1.0.0"
REPO_URL="https://github.com/username/personal-ai-agent"

echo -e "${BLUE}🚀 ${PROJECT_NAME} - Quick Start Setup${NC}"
echo -e "${BLUE}===========================================${NC}"
echo -e "Version: ${VERSION}"
echo -e "Hybrid Deployment: Vercel Frontend + Local Backend\n"

# Function to print colored messages
print_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."
    
    local errors=0
    
    # Check Python
    if ! command_exists python3; then
        print_error "Python 3.8+ is required. Please install Python first."
        echo "  - macOS: brew install python3"
        echo "  - Ubuntu/Debian: sudo apt install python3 python3-pip"
        echo "  - Windows: Download from https://python.org"
        errors=$((errors + 1))
    else
        python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        if [ "$(printf '%s\n' "3.8" "$python_version" | sort -V | head -n1)" != "3.8" ]; then
            print_error "Python 3.8+ required. Current version: $python_version"
            errors=$((errors + 1))
        else
            print_success "Python $python_version found"
        fi
    fi
    
    # Check Node.js (for frontend development)
    if ! command_exists node; then
        print_warning "Node.js not found. Install if you plan to develop the frontend locally."
        echo "  - Install from: https://nodejs.org"
    else
        node_version=$(node --version)
        print_success "Node.js $node_version found"
    fi
    
    # Check Git
    if ! command_exists git; then
        print_error "Git is required for version control."
        errors=$((errors + 1))
    else
        print_success "Git found"
    fi
    
    # Check available disk space (models are ~4GB)
    available_space=$(df . | tail -1 | awk '{print $4}')
    required_space=4194304  # 4GB in KB
    
    if [ "$available_space" -lt "$required_space" ]; then
        print_error "Insufficient disk space. Need at least 4GB for AI models."
        errors=$((errors + 1))
    else
        print_success "Sufficient disk space available"
    fi
    
    if [ $errors -gt 0 ]; then
        print_error "Prerequisites check failed. Please resolve the issues above."
        exit 1
    fi
    
    print_success "All prerequisites met!"
}

# Setup backend
setup_backend() {
    print_step "Setting up backend..."
    
    cd backend
    
    # Create virtual environment
    print_step "Creating Python virtual environment..."
    python3 -m venv .venv
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    print_step "Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Setup environment file
    if [ ! -f .env ]; then
        print_step "Creating environment configuration..."
        cp .env.example .env
        print_success "Environment file created from template"
        print_warning "Edit backend/.env to configure Gmail OAuth (optional)"
    else
        print_success "Environment file already exists"
    fi
    
    # Download AI models
    print_step "Downloading AI models (this may take several minutes)..."
    print_warning "Downloading Mistral 7B model (~4GB) and embedding model (~500MB)"
    
    # Download LLM model
    python download_model.py
    print_success "LLM model downloaded"
    
    # Download embedding model
    python download_embedding_model.py
    print_success "Embedding model downloaded"
    
    # Setup database
    print_step "Initializing database..."
    python setup_db.py
    print_success "Database initialized"
    
    # Return to root directory
    cd ..
    
    print_success "Backend setup completed!"
}

# Setup frontend (optional, for local development)
setup_frontend() {
    print_step "Setting up frontend (optional for local development)..."
    
    if ! command_exists node; then
        print_warning "Node.js not found. Skipping frontend setup."
        print_warning "Frontend will be deployed to Vercel directly from repository."
        return
    fi
    
    cd frontend
    
    # Install dependencies
    if [ -f package.json ]; then
        print_step "Installing frontend dependencies..."
        npm install
        
        # Setup environment file
        if [ ! -f .env.local ]; then
            print_step "Creating frontend environment configuration..."
            cp .env.local.example .env.local
            print_success "Frontend environment file created"
        fi
        
        print_success "Frontend setup completed!"
        print_step "You can run 'npm run dev' in the frontend/ directory for local development"
    else
        print_warning "Frontend package.json not found. Skipping frontend setup."
    fi
    
    cd ..
}

# Create useful scripts
create_scripts() {
    print_step "Creating convenience scripts..."
    
    # Backend start script
    cat > start-backend.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting Personal AI Agent Backend..."
cd backend
source .venv/bin/activate
python main.py
EOF
    chmod +x start-backend.sh
    
    # Backend stop script (for later use)
    cat > stop-backend.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping Personal AI Agent Backend..."
pkill -f "python main.py" || echo "Backend was not running"
EOF
    chmod +x stop-backend.sh
    
    # Create admin user script
    cat > create-admin.sh << 'EOF'
#!/bin/bash
echo "👤 Creating admin user..."
cd backend
source .venv/bin/activate
python create_admin.py
EOF
    chmod +x create-admin.sh
    
    print_success "Convenience scripts created!"
}

# Display next steps
show_next_steps() {
    echo ""
    echo -e "${GREEN}🎉 Setup completed successfully!${NC}"
    echo -e "${GREEN}=================================${NC}"
    echo ""
    echo -e "${BLUE}📝 Next Steps:${NC}"
    echo ""
    echo -e "${YELLOW}1. Create your user account:${NC}"
    echo "   ./create-admin.sh"
    echo ""
    echo -e "${YELLOW}2. Start the backend:${NC}"
    echo "   ./start-backend.sh"
    echo "   (Backend will be available at: http://localhost:8000)"
    echo ""
    echo -e "${YELLOW}3. Deploy frontend to Vercel:${NC}"
    echo "   - Push this repository to GitHub"
    echo "   - Connect to Vercel (vercel.com)"
    echo "   - Deploy the frontend/ directory"
    echo "   - Set environment variable: NEXT_PUBLIC_API_URL=http://localhost:8000"
    echo ""
    echo -e "${YELLOW}4. Optional - Gmail Integration:${NC}"
    echo "   - Edit backend/.env with your Gmail OAuth credentials"
    echo "   - See docs/gmail-integration.md for setup guide"
    echo ""
    echo -e "${BLUE}📚 Documentation:${NC}"
    echo "   - Project Overview: README.md"
    echo "   - Deployment Guide: HYBRID_DEPLOYMENT.md"
    echo "   - API Documentation: docs/api/"
    echo "   - Troubleshooting: docs/troubleshooting.md"
    echo ""
    echo -e "${BLUE}🔧 Development:${NC}"
    echo "   - Frontend dev: cd frontend && npm run dev"
    echo "   - Backend dev: cd backend && source .venv/bin/activate && python main.py"
    echo ""
    echo -e "${GREEN}Happy coding! 🚀${NC}"
}

# Main execution
main() {
    # Check if we're in the right directory
    if [ ! -f "README.md" ] || [ ! -d "backend" ]; then
        print_error "Please run this script from the root of the Personal AI Agent repository"
        exit 1
    fi
    
    # Run setup steps
    check_prerequisites
    setup_backend
    setup_frontend
    create_scripts
    show_next_steps
}

# Handle interruption
trap 'echo -e "\n${RED}Setup interrupted. You can resume by running this script again.${NC}"; exit 1' INT

# Run main function
main "$@"