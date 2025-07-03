#!/bin/bash

# WebConsole Development Setup Script
# This script sets up the development environment for WebConsole

set -e

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

# Check if running from WebConsole directory
if [[ ! -f "component.yaml" ]] || [[ ! -d "backend" ]] || [[ ! -d "frontend" ]]; then
    print_error "This script must be run from the WebConsole component directory"
    exit 1
fi

print_status "Starting WebConsole development environment setup..."

# Check system requirements
print_status "Checking system requirements..."

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3.11+ is required but not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [[ $(echo "$PYTHON_VERSION < 3.11" | bc -l) -eq 1 ]]; then
    print_error "Python 3.11+ is required, but version $PYTHON_VERSION is installed"
    exit 1
fi
print_success "Python $PYTHON_VERSION found"

# Check Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js 18+ is required but not installed"
    exit 1
fi

NODE_VERSION=$(node -v | sed 's/v//')
if [[ $(echo "$NODE_VERSION < 18.0.0" | bc -l) -eq 1 ]]; then
    print_error "Node.js 18+ is required, but version $NODE_VERSION is installed"
    exit 1
fi
print_success "Node.js $NODE_VERSION found"

# Check npm
if ! command -v npm &> /dev/null; then
    print_error "npm is required but not installed"
    exit 1
fi
print_success "npm $(npm -v) found"

# Create necessary directories
print_status "Creating project directories..."
mkdir -p data logs config/{development,production} data/{uploads,backups}
print_success "Directories created"

# Setup backend
print_status "Setting up backend environment..."
cd backend

# Create virtual environment if it doesn't exist
if [[ ! -d "venv" ]]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
print_success "Python dependencies installed"

# Copy environment file
if [[ ! -f ".env" ]]; then
    print_status "Creating backend .env file..."
    cp .env.example .env
    print_warning "Please edit backend/.env with your configuration"
fi

cd ..

# Setup frontend
print_status "Setting up frontend environment..."
cd frontend

# Install Node.js dependencies
print_status "Installing Node.js dependencies..."
npm install
print_success "Node.js dependencies installed"

# Copy environment file
if [[ ! -f ".env" ]]; then
    print_status "Creating frontend .env file..."
    cp .env.example .env
    print_warning "Please edit frontend/.env with your configuration"
fi

cd ..

# Setup development services (optional)
print_status "Setting up development services..."

# Check if Docker is available
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    print_status "Docker found, setting up development services..."
    
    # Create development docker-compose override
    cat > docker-compose.dev.yml << EOF
version: '3.8'

services:
  postgres:
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=webconsole_dev
      - POSTGRES_USER=dev
      - POSTGRES_PASSWORD=dev

  redis:
    ports:
      - "6379:6379"
    command: redis-server --requirepass dev

networks:
  webconsole-network:
    driver: bridge
EOF

    print_success "Development docker-compose created"
    print_status "To start development services, run: docker-compose -f docker-compose.dev.yml up -d"
else
    print_warning "Docker not found. You'll need to manually setup PostgreSQL and Redis for development"
fi

# Create development scripts
print_status "Creating development scripts..."

# Backend development script
cat > scripts/dev-backend.sh << 'EOF'
#!/bin/bash
cd backend
source venv/bin/activate
export PYTHONPATH="$PWD:$PYTHONPATH"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
EOF

# Frontend development script
cat > scripts/dev-frontend.sh << 'EOF'
#!/bin/bash
cd frontend
npm run dev
EOF

# Full development script
cat > scripts/dev-start.sh << 'EOF'
#!/bin/bash
echo "Starting WebConsole development servers..."

# Start backend in background
./scripts/dev-backend.sh &
BACKEND_PID=$!

# Start frontend in background
./scripts/dev-frontend.sh &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"

# Function to cleanup on exit
cleanup() {
    echo "Stopping development servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

# Trap cleanup function on script exit
trap cleanup SIGINT SIGTERM

# Wait for processes
wait
EOF

# Make scripts executable
chmod +x scripts/dev-*.sh

print_success "Development scripts created"

# Create VS Code configuration
print_status "Creating VS Code configuration..."
mkdir -p .vscode

cat > .vscode/settings.json << EOF
{
    "python.defaultInterpreterPath": "./backend/venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    "eslint.workingDirectories": ["frontend"],
    "prettier.configPath": "./frontend/.prettierrc",
    "typescript.preferences.importModuleSpecifier": "relative",
    "vue.codeActions.enabled": true,
    "files.associations": {
        "*.yaml": "yaml",
        "*.yml": "yaml"
    },
    "yaml.schemas": {
        "./component.yaml": "component.yaml"
    }
}
EOF

cat > .vscode/launch.json << EOF
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug Backend",
            "type": "python",
            "request": "launch",
            "program": "\${workspaceFolder}/backend/venv/bin/uvicorn",
            "args": ["app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8080"],
            "cwd": "\${workspaceFolder}/backend",
            "env": {
                "PYTHONPATH": "\${workspaceFolder}/backend"
            },
            "console": "integratedTerminal"
        }
    ]
}
EOF

print_success "VS Code configuration created"

# Final instructions
print_success "WebConsole development environment setup complete!"
echo
print_status "Next steps:"
echo "1. Edit backend/.env and frontend/.env with your configuration"
echo "2. Start development services (if using Docker): docker-compose -f docker-compose.dev.yml up -d"
echo "3. Start development servers: ./scripts/dev-start.sh"
echo "4. Access the application:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8080"
echo "   - API Docs: http://localhost:8080/docs"
echo
print_warning "Don't forget to configure your Aetherius Core integration settings!"