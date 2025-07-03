#!/bin/bash

# Aetherius Component: Web Setup Script
# This script sets up the development environment

set -e

echo "🔧 Setting up Aetherius Component: Web Development Environment"
echo "=============================================================="

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check dependencies
echo "📋 Checking system dependencies..."

if ! command_exists python3; then
    echo "❌ Python 3 is not installed"
    echo "   Please install Python 3.8+ from https://python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python version $PYTHON_VERSION is too old (required: $REQUIRED_VERSION+)"
    exit 1
fi

if ! command_exists node; then
    echo "❌ Node.js is not installed"
    echo "   Please install Node.js 18+ from https://nodejs.org"
    exit 1
fi

NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version is too old (required: 18+)"
    exit 1
fi

if ! command_exists npm; then
    echo "❌ npm is not installed"
    echo "   npm should come with Node.js installation"
    exit 1
fi

echo "✅ All system dependencies found"
echo "   Python: $(python3 --version)"
echo "   Node.js: $(node --version)"
echo "   npm: $(npm --version)"

# Setup backend
echo ""
echo "🐍 Setting up backend environment..."

cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Mark as installed
touch venv/installed

echo "✅ Backend setup complete"

cd ..

# Setup frontend
echo ""
echo "🎨 Setting up frontend environment..."

cd frontend

# Install dependencies
echo "📦 Installing Node.js dependencies..."
npm install

echo "✅ Frontend setup complete"

cd ..

# Create additional directories
echo ""
echo "📁 Creating additional directories..."

mkdir -p logs
mkdir -p data
mkdir -p temp

echo "✅ Additional directories created"

# Create environment file templates
echo ""
echo "📝 Creating configuration templates..."

# Backend environment template
cat > backend/.env.example << EOF
# Backend Configuration
DEBUG=true
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Core Integration
CORE_HOST=localhost
CORE_PORT=25575
CORE_TIMEOUT=30

# Security
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# Database (if needed in future)
DATABASE_URL=sqlite:///./data/web_component.db
EOF

# Frontend environment template
cat > frontend/.env.example << EOF
# Frontend Configuration
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_BASE_URL=ws://localhost:8000
VITE_APP_TITLE=Aetherius Web Console
VITE_APP_VERSION=0.1.0
EOF

echo "✅ Configuration templates created"
echo "   Backend: backend/.env.example"
echo "   Frontend: frontend/.env.example"

# Success message
echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Review and customize configuration files:"
echo "   - Copy backend/.env.example to backend/.env"
echo "   - Copy frontend/.env.example to frontend/.env"
echo ""
echo "2. Start the development environment:"
echo "   ./scripts/start-dev.sh"
echo ""
echo "3. Access the application:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000"
echo "   - API Documentation: http://localhost:8000/docs"
echo ""
echo "For more information, see README.md"