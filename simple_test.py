#!/usr/bin/env python3
"""
Simple MCP Server Test Client
Test the server without complex dependencies
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_basic_endpoints():
    """Test basic endpoints that don't require ML models"""
    print("🧪 MCP Server Basic Test Client")
    print("=" * 40)

    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ Health check: PASS")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check: FAIL ({response.status_code})")
    except Exception as e:
        print(f"❌ Health check: ERROR - {e}")

    # Test 2: Root endpoint
    print("\n2. Testing root endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ Root endpoint: PASS")
        else:
            print(f"❌ Root endpoint: FAIL ({response.status_code})")
    except Exception as e:
        print(f"❌ Root endpoint: ERROR - {e}")

    # Test 3: List memories (should be empty initially)
    print("\n3. Testing list memories...")
    try:
        response = requests.get(f"{BASE_URL}/memories/test_user")
        if response.status_code == 200:
            data = response.json()
            print("✅ List memories: PASS")
            print(f"   Memories found: {len(data.get('memories', []))}")
        else:
            print(f"❌ List memories: FAIL ({response.status_code})")
    except Exception as e:
        print(f"❌ List memories: ERROR - {e}")

def test_with_sample_data():
    """Test with sample data (may fail if ML models not working)"""
    print("\n" + "=" * 40)
    print("🧪 Testing with Sample Data")
    print("=" * 40)

    # Test store memory
    print("\n4. Testing store memory...")
    test_content = "This is a test memory about Python programming."
    payload = {
        "user_id": "test_user",
        "content": test_content
    }

    try:
        response = requests.post(
            f"{BASE_URL}/store_memory",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            print("✅ Store memory: PASS")
            result = response.json()
            print(f"   Memory ID: {result.get('memory_id', 'N/A')}")
            print(f"   Summary: {result.get('summary', 'N/A')[:50]}...")
        else:
            print(f"❌ Store memory: FAIL ({response.status_code})")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Store memory: ERROR - {e}")

    # Wait a moment
    time.sleep(1)

    # Test search memory
    print("\n5. Testing search memory...")
    search_payload = {
        "user_id": "test_user",
        "query": "Python programming"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/search_memory",
            json=search_payload,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            print("✅ Search memory: PASS")
            results = response.json().get('results', [])
            print(f"   Results found: {len(results)}")
            if results:
                print(f"   First result: {results[0].get('content', '')[:50]}...")
        else:
            print(f"❌ Search memory: FAIL ({response.status_code})")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Search memory: ERROR - {e}")

def show_manual_test_commands():
    """Show manual curl commands for testing"""
    print("\n" + "=" * 40)
    print("🔧 Manual Test Commands (curl)")
    print("=" * 40)

    print("""
# 1. Health check
curl http://localhost:8000/

# 2. List memories for a user
curl http://localhost:8000/memories/test_user

# 3. Store a memory
curl -X POST http://localhost:8000/store_memory \\
  -H "Content-Type: application/json" \\
  -d '{"user_id":"test_user","content":"I love coding in Python!"}'

# 4. Search memories
curl -X POST http://localhost:8000/search_memory \\
  -H "Content-Type: application/json" \\
  -d '{"user_id":"test_user","query":"Python"}'

# 5. Get specific memory
curl http://localhost:8000/memories/test_user/memory_123

# 6. Stream endpoint (Server-Sent Events)
curl -N http://localhost:8000/stream
""")

if __name__ == "__main__":
    print("Make sure the MCP server is running first!")
    print("Run: cd mcp-server && python3 main.py")
    print("Then run this script in another terminal")
    print()

    test_basic_endpoints()
    test_with_sample_data()
    show_manual_test_commands()

    print("\n" + "=" * 40)
    print("📖 Additional Testing Options:")
    print("1. Open http://localhost:8000/docs in your browser (FastAPI auto-docs)")
    print("2. Use Postman or Insomnia to test the API")
    print("3. Use the curl commands above")
    print("=" * 40)