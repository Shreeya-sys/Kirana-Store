"""
Test script to diagnose /token endpoint issues
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_token_endpoint():
    """Test the /token endpoint and diagnose issues"""
    
    print("=" * 50)
    print("Testing /token Endpoint")
    print("=" * 50)
    
    # Test data
    username = "shreeya"
    password = "shreeya"
    
    # Try to get token
    print(f"\n1. Attempting to get token for user: {username}")
    print("-" * 50)
    
    try:
        response = requests.post(
            f"{BASE_URL}/token",
            headers={
                "accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "grant_type": "password",
                "username": username,
                "password": password,
                "scope": "",
                "client_id": "bearer",
                "client_secret": ""
            }
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"\n✅ SUCCESS!")
            print(f"Access Token: {token_data.get('access_token', 'N/A')[:50]}...")
            print(f"Token Type: {token_data.get('token_type', 'N/A')}")
        else:
            print(f"\n❌ FAILED!")
            error_detail = response.json().get('detail', 'Unknown error')
            print(f"Error: {error_detail}")
            
            # Diagnose the issue
            if "Incorrect username or password" in error_detail:
                print("\n🔍 Diagnosis:")
                print("   - User might not exist")
                print("   - Password might be incorrect")
                print("   - User might have been created with different password")
                
                # Check if user exists
                print("\n2. Checking if user exists...")
                check_user_response = requests.get(f"{BASE_URL}/users/me")
                print(f"   (This requires authentication, so it won't work without token)")
                
                print("\n💡 Solution:")
                print("   Create the user first:")
                print(f"   curl -X POST '{BASE_URL}/users/' \\")
                print(f"     -H 'Content-Type: application/json' \\")
                print(f"     -d '{{'")
                print(f"       \"username\": \"{username}\",")
                print(f"       \"password\": \"{password}\",")
                print(f"       \"role\": \"admin\"")
                print(f"     }}'")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error!")
        print("   Make sure the backend server is running on http://127.0.0.1:8000")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_token_endpoint()
