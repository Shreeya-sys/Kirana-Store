#!/usr/bin/env python3
"""
Backend Connection Test Script
Tests if the backend is running and accessible
"""

import sys
import urllib.request
import urllib.error
import json

BACKEND_URL = "http://127.0.0.1:8000"

def test_endpoint(url, method="GET", data=None, description=""):
    """Test a backend endpoint"""
    try:
        if data:
            req = urllib.request.Request(url, data=json.dumps(data).encode(), 
                                       headers={'Content-Type': 'application/json'})
        else:
            req = urllib.request.Request(url)
        
        with urllib.request.urlopen(req, timeout=5) as response:
            status = response.getcode()
            content = response.read().decode()
            print(f"✓ {description}: {status} OK")
            if content and len(content) < 200:
                print(f"  Response: {content[:100]}")
            return True
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print(f"✓ {description}: 401 (Expected - requires authentication)")
            return True
        else:
            print(f"✗ {description}: {e.code} {e.reason}")
            return False
    except urllib.error.URLError as e:
        print(f"✗ {description}: Connection failed - {e.reason}")
        return False
    except Exception as e:
        print(f"✗ {description}: Error - {str(e)}")
        return False

def main():
    print("=" * 50)
    print("Backend Connection Test")
    print("=" * 50)
    
    results = []
    
    # Test 1: Root endpoint
    print("\n1. Testing root endpoint...")
    results.append(test_endpoint(f"{BACKEND_URL}/", description="Root endpoint"))
    
    # Test 2: API docs
    print("\n2. Testing API documentation...")
    results.append(test_endpoint(f"{BACKEND_URL}/docs", description="Swagger UI"))
    
    # Test 3: OpenAPI schema
    print("\n3. Testing OpenAPI schema...")
    results.append(test_endpoint(f"{BACKEND_URL}/openapi.json", description="OpenAPI schema"))
    
    # Test 4: Login endpoint (should fail with 401 for invalid creds)
    print("\n4. Testing login endpoint...")
    try:
        login_data = "username=test&password=test"
        req = urllib.request.Request(
            f"{BACKEND_URL}/token",
            data=login_data.encode(),
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            print("⚠ Login endpoint: Unexpected success (should require valid credentials)")
            results.append(False)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("✓ Login endpoint: 401 (Correct - invalid credentials rejected)")
            results.append(True)
        else:
            print(f"⚠ Login endpoint: {e.code} (Unexpected status)")
            results.append(False)
    except Exception as e:
        print(f"✗ Login endpoint: Error - {str(e)}")
        results.append(False)
    
    # Test 5: User creation (test endpoint)
    print("\n5. Testing user creation endpoint...")
    import random
    test_username = f"testuser_{random.randint(1000, 9999)}"
    user_data = {
        "username": test_username,
        "password": "testpass123",
        "role": "staff"
    }
    results.append(test_endpoint(
        f"{BACKEND_URL}/users/",
        method="POST",
        data=user_data,
        description="User creation"
    ))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! Backend is ready.")
        print("\nFrontend API client is configured to connect to:")
        print(f"  {BACKEND_URL}")
        print("\nYou can now:")
        print("  1. Start frontend: cd frontend && flutter run")
        print("  2. Create users via: http://127.0.0.1:8000/docs")
        return 0
    else:
        print("⚠ Some tests failed. Please check backend is running:")
        print("  cd backend")
        print("  uvicorn main:app --reload")
        return 1

if __name__ == "__main__":
    sys.exit(main())
