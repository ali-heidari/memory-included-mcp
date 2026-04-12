#!/bin/bash
# MCP Server Test Runner
# This script starts the server and runs comprehensive tests

echo "🚀 MCP Memory Server Test Suite"
echo "================================="

# Check if we're in the right directory
if [ ! -f "mcp_server/main.py" ]; then
    echo "❌ Error: Run this script from the project root directory"
    echo "   cd /path/to/mendix-agent"
    exit 1
fi

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🧹 Cleaning up..."
    kill $SERVER_PID 2>/dev/null
    exit
}

# Set trap to cleanup on script exit
trap cleanup EXIT INT TERM

echo "🔧 Starting MCP Server..."
cd mcp-server
python3 main.py &
SERVER_PID=$!

echo "⏳ Waiting for server to start..."
sleep 5

# Check if server is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Server failed to start"
    exit 1
fi

echo "✅ Server is running on http://localhost:8000"
echo ""

# Run the test script
cd ..
python3 test_mcp_server.py

echo ""
echo "🎯 Test complete! Server is still running on http://localhost:8000"
echo "📖 View API docs at: http://localhost:8000/docs"
echo "🛑 Press Ctrl+C to stop the server"