#!/usr/bin/env python3
"""
Simple test runner for MCP server
"""

import sys
import os

# Get the project root directory (parent of this script)
project_root = os.path.dirname(os.path.abspath(__file__))

# Add project root to Python path so we can import mcp_server
sys.path.insert(0, project_root)

# Add user packages to path
sys.path.insert(0, '/home/elpixeler/.local/lib/python3.10/site-packages')

# Also add system packages
sys.path.insert(0, '/usr/lib/python3/dist-packages')

if __name__ == "__main__":
    # Change to project root directory
    os.chdir(project_root)

    import pytest
    sys.exit(pytest.main(["-v", "--tb=short", "tests/"]))