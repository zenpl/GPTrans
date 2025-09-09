#!/usr/bin/env python3
"""
Test script to verify the server can start
"""
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_server_startup():
    """Test that the FastAPI server can be instantiated."""
    try:
        print("Testing FastAPI server startup...")
        
        from app.backend.main import app
        
        # Check if app is created
        assert app is not None
        print("✅ FastAPI app created successfully")
        
        # Check routes exist
        routes = [route.path for route in app.routes]
        expected_routes = ["/api/health", "/api/upload"]
        
        for expected in expected_routes:
            if any(expected in route for route in routes):
                print(f"✅ Route {expected} found")
            else:
                print(f"❌ Route {expected} not found")
        
        print(f"\n📋 Available routes:")
        for route in routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                methods = getattr(route, 'methods', ['GET'])
                print(f"  {', '.join(methods)} {route.path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Server startup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_server_startup()
    sys.exit(0 if success else 1)