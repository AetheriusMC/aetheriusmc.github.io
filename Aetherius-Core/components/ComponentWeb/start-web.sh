#!/bin/bash

# Aetherius Web Component - One-Click Startup Script
# This script provides a simple one-click solution to start both frontend and backend

set -e

echo "🚀 Aetherius Web Component - One-Click Startup"
echo "=============================================="

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

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

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to get process info for a port
get_port_processes() {
    lsof -ti :$1 2>/dev/null
}

# Function to kill processes on a port
kill_port_processes() {
    local port=$1
    local processes=$(get_port_processes $port)
    
    if [ -n "$processes" ]; then
        print_warning "Port $port is in use. Killing existing processes..."
        echo "$processes" | xargs kill -9 2>/dev/null || true
        sleep 2
        
        # Verify processes are killed
        if port_in_use $port; then
            print_error "Failed to free port $port"
            return 1
        else
            print_success "Port $port freed"
        fi
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            print_success "$name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 1
        ((attempt++))
    done
    
    print_error "$name failed to start within $max_attempts seconds"
    return 1
}

# Function to wait for port to be listening
wait_for_port() {
    local port=$1
    local name=$2
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $name (port $port) to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if lsof -i :$port >/dev/null 2>&1; then
            print_success "$name is listening on port $port!"
            return 0
        fi
        
        echo -n "."
        sleep 1
        ((attempt++))
    done
    
    print_error "$name failed to start on port $port within $max_attempts seconds"
    return 1
}

# Function to detect actual frontend port from logs
detect_frontend_port() {
    local log_file="../logs/frontend.log"
    local max_attempts=30
    local attempt=1
    
    print_status "Detecting actual frontend port..."
    
    while [ $attempt -le $max_attempts ]; do
        if [ -f "$log_file" ]; then
            # Look for "Local: http://localhost:XXXX/" pattern
            local detected_port=$(grep -o "Local:.*http://localhost:[0-9]*/" "$log_file" | grep -o "[0-9]*" | tail -1)
            if [ ! -z "$detected_port" ]; then
                echo "$detected_port"
                return 0
            fi
        fi
        
        sleep 1
        ((attempt++))
    done
    
    # Default fallback
    echo "3000"
    return 1
}

# Function to cleanup on exit
cleanup() {
    echo ""
    print_status "Stopping services..."
    
    # Kill background processes
    if [ ! -z "$BACKEND_PID" ] && kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    # Kill any remaining processes on our ports
    kill_port_processes 8080 >/dev/null 2>&1 || true
    if [ ! -z "$FRONTEND_PORT" ]; then
        kill_port_processes $FRONTEND_PORT >/dev/null 2>&1 || true
    fi
    
    print_success "Services stopped"
    exit 0
}

# Set up cleanup trap
trap cleanup EXIT INT TERM

# Check dependencies
print_status "Checking dependencies..."

if ! command_exists python3; then
    print_error "Python 3 is not installed"
    exit 1
fi

if ! command_exists node; then
    print_error "Node.js is not installed"
    exit 1
fi

if ! command_exists npm; then
    print_error "npm is not installed"
    exit 1
fi

print_success "All dependencies found"

# Free required ports
print_status "Preparing ports..."
kill_port_processes 8080
kill_port_processes 3000

# Setup backend environment
print_status "Setting up backend environment..."

cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install backend dependencies
if [ ! -f "venv/installed" ] || [ "requirements.txt" -nt "venv/installed" ]; then
    print_status "Installing backend dependencies..."
    pip install -r requirements.txt
    touch venv/installed
    print_success "Backend dependencies installed"
else
    print_success "Backend dependencies already up to date"
fi

cd ..

# Setup frontend environment
print_status "Setting up frontend environment..."

cd frontend

# Install frontend dependencies
if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules" ]; then
    print_status "Installing frontend dependencies..."
    npm install
    print_success "Frontend dependencies installed"
else
    print_success "Frontend dependencies already up to date"
fi

cd ..

# Start backend
print_status "Starting backend server..."
cd backend
source venv/bin/activate

# Create logs directory if it doesn't exist
mkdir -p ../logs

# Start backend in background
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!

cd ..

# Wait for backend to be ready
if ! wait_for_service "http://localhost:8080/health" "Backend"; then
    print_error "Backend failed to start"
    exit 1
fi

# Start frontend
print_status "Starting frontend server..."
cd frontend

# Create logs directory if it doesn't exist (if not already created)
mkdir -p ../logs

# Start frontend in background
nohup npm run dev -- --host 0.0.0.0 --port 3000 > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!

cd ..

# Wait for frontend to be ready on port 3000
if ! wait_for_port 3000 "Frontend"; then
    # If port 3000 failed, try to detect the actual port
    FRONTEND_PORT=$(detect_frontend_port)
    print_warning "Frontend not on port 3000, detected on port $FRONTEND_PORT"
    
    if ! wait_for_port $FRONTEND_PORT "Frontend"; then
        print_error "Frontend failed to start"
        exit 1
    fi
else
    FRONTEND_PORT=3000
fi


# Success message
echo ""
echo "🎉 Aetherius Web Component Started Successfully!"
echo "============================================="
echo ""
echo "📱 Frontend:  http://localhost:$FRONTEND_PORT"
echo "🔧 Backend:   http://localhost:8080"
echo "📚 API Docs:  http://localhost:8080/docs"
echo ""
echo "📋 Logs:"
echo "   Backend:  logs/backend.log"
echo "   Frontend: logs/frontend.log"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Monitor processes
while true; do
    # Check if backend is still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        print_error "Backend process died unexpectedly"
        break
    fi
    
    # Check if frontend is still running
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        print_error "Frontend process died unexpectedly"
        break
    fi
    
    sleep 5
done

# If we get here, something went wrong
print_error "One or more services stopped unexpectedly"
exit 1