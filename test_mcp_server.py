#!/usr/bin/env python3
"""
Test script for MCP Memory Server
Run this to test all endpoints without Mendix
"""

import requests
import json
import time
import subprocess
import sys
import os

# Server configuration
BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_store_memory():
    """Test storing memory"""
    print("\n💾 Testing store_memory endpoint...")

    test_data = {
        "user_id": "test_user_123",
        "content": "I love using dark mode in applications because it reduces eye strain and looks more professional."
    }

    try:
        response = requests.post(
            f"{BASE_URL}/store_memory",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ Store memory successful")
            print(f"   Memory ID: {result['id']}")
            print(f"   Summary: {result['summary']}")
            return result['id']
        else:
            print(f"❌ Store memory failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Store memory error: {e}")
        return None

def test_search_memory(memory_id):
    """Test searching memories"""
    print("\n🔍 Testing search_memory endpoint...")

    search_data = {
        "user_id": "test_user_123",
        "query": "dark mode preferences",
        "limit": 5
    }

    try:
        response = requests.post(
            f"{BASE_URL}/search_memory",
            json=search_data,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ Search memory successful")
            print(f"   Found {result['total_found']} memories")

            for i, memory in enumerate(result['results'][:3]):  # Show first 3
                print(f"   {i+1}. {memory['summary']} (similarity: {memory['similarity']:.2f})")

            return True
        else:
            print(f"❌ Search memory failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Search memory error: {e}")
        return False

def test_list_memories():
    """Test listing all memories for a user"""
    print("\n📋 Testing list memories endpoint...")

    try:
        response = requests.get(f"{BASE_URL}/memories/test_user_123")

        if response.status_code == 200:
            result = response.json()
            print("✅ List memories successful")
            print(f"   User has {result['count']} memories")

            for i, memory in enumerate(result['memories'][:2]):  # Show first 2
                print(f"   {i+1}. {memory['summary'][:50]}...")

            return True
        else:
            print(f"❌ List memories failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ List memories error: {e}")
        return False

def test_stream():
    """Test streaming endpoint"""
    print("\n🌊 Testing stream endpoint...")

    try:
        response = requests.get(f"{BASE_URL}/stream", stream=True, timeout=5)

        if response.status_code == 200:
            print("✅ Stream endpoint accessible")
            # Read a few chunks
            chunks = 0
            for line in response.iter_lines():
                if line:
                    chunks += 1
                    if chunks >= 3:  # Show first 3 chunks
                        break
            print(f"   Received {chunks} data chunks")
            return True
        else:
            print(f"❌ Stream failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Stream error: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("🚀 Starting MCP Server Tests")
    print("=" * 50)

    # Test 1: Health
    if not test_health():
        print("❌ Server not responding. Make sure it's running on port 8000")
        return False

    # Test 2: Store memory
    memory_id = test_store_memory()
    if not memory_id:
        print("❌ Cannot continue without successful store")
        return False

    # Test 3: Search memory
    if not test_search_memory(memory_id):
        print("⚠️ Search failed, but continuing...")

    # Test 4: List memories
    if not test_list_memories():
        print("⚠️ List failed, but continuing...")

    # Test 5: Stream
    if not test_stream():
        print("⚠️ Stream failed, but continuing...")

    print("\n" + "=" * 50)
    print("🎉 MCP Server testing complete!")
    print("\n📖 API Documentation: http://localhost:8000/docs")
    print("🔄 ReDoc: http://localhost:8000/redoc")

    return True

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)