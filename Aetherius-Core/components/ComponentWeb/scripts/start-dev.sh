#!/bin/bash

# Aetherius Component: Web Development Startup Script
# This script starts both backend and frontend in development mode

set -e

echo "🚀 Starting Aetherius Component: Web Development Environment"
echo "============================================================"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to kill processes using a specific port with user confirmation
kill_port() {
    local port=$1
    local processes=$(lsof -ti :$port 2>/dev/null)
    
    if [ -n "$processes" ]; then
        echo "🔍 Found processes using port $port:"
        lsof -i :$port
        echo ""
        read -p "❓ Do you want to kill these processes? (y/N): " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "🔥 Killing processes using port $port..."
            echo "$processes" | xargs kill -9 2>/dev/null || true
            sleep 1
            echo "✅ Processes killed"
        else
            echo "❌ Operation cancelled. Port $port will remain in use."
            return 1
        fi
    fi
}

# Check dependencies
echo "📋 Checking dependencies..."

if ! command_exists python3; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

if ! command_exists node; then
    echo "❌ Node.js is not installed"
    exit 1
fi

if ! command_exists npm; then
    echo "❌ npm is not installed"
    exit 1
fi

echo "✅ All dependencies found"

# Check for virtual environment
if [ ! -d "backend/venv" ]; then
    echo "📦 Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    cd ..
fi

# Activate virtual environment and install dependencies
echo "📦 Setting up backend dependencies..."
cd backend
source venv/bin/activate

if [ ! -f "venv/installed" ]; then
    pip install -r requirements.txt
    touch venv/installed
    echo "✅ Backend dependencies installed"
else
    echo "✅ Backend dependencies already installed"
fi

cd ..

# Install frontend dependencies
echo "📦 Setting up frontend dependencies..."
cd frontend

if [ ! -d "node_modules" ]; then
    npm install
    echo "✅ Frontend dependencies installed"
else
    echo "✅ Frontend dependencies already installed"
fi

cd ..

# Check required ports and ask for confirmation if needed
echo "🔍 Checking required ports..."

backend_port_clear=true
frontend_port_clear=true

if port_in_use 8080; then
    echo "⚠️  Port 8080 is in use by another process"
    if ! kill_port 8080; then
        backend_port_clear=false
    fi
fi

if port_in_use 3000; then
    echo "⚠️  Port 3000 is in use by another process"
    if ! kill_port 3000; then
        frontend_port_clear=false
    fi
fi

# Check if we can proceed
if [ "$backend_port_clear" = false ] || [ "$frontend_port_clear" = false ]; then
    echo ""
    echo "❌ Cannot start services - required ports are in use"
    echo "   Please stop the conflicting processes manually or restart with different ports"
    exit 1
fi

echo ""
echo "🎯 Starting services..."
echo "   Backend:  http://localhost:8080"
echo "   Frontend: http://localhost:3000"
echo "   API Docs: http://localhost:8080/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $(jobs -p) 2>/dev/null || true
    wait
    echo "✅ Services stopped"
}

trap cleanup EXIT

# Start backend
echo "🔧 Starting backend server..."
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 2

# Start frontend
echo "🎨 Starting frontend development server..."
cd frontend
npm run dev -- --port 3000 &
FRONTEND_PID=$!
cd ..

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID