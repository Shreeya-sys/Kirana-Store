"""
Script to diagnose and fix user authentication issues
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
import crud
import schemas
import auth

def diagnose_and_fix():
    """Diagnose and fix user authentication"""
    db = SessionLocal()
    try:
        username = "shreeya"
        password = "shreeya"
        
        print("=" * 60)
        print("User Authentication Diagnostic Tool")
        print("=" * 60)
        
        # Check if user exists
        print(f"\n1. Checking if user '{username}' exists...")
        user = crud.get_user_by_username(db, username=username)
        
        if not user:
            print("   ❌ User does NOT exist!")
            print("\n   Creating user...")
            
            try:
                user_data = schemas.UserCreate(
                    username=username,
                    password=password,
                    role="admin"
                )
                user = crud.create_user(db, user_data)
                print(f"   ✅ User created successfully!")
                print(f"      ID: {user.id}")
                print(f"      Username: {user.username}")
                print(f"      Role: {user.role}")
            except Exception as e:
                print(f"   ❌ Failed to create user: {e}")
                return
        else:
            print(f"   ✅ User exists!")
            print(f"      ID: {user.id}")
            print(f"      Username: {user.username}")
            print(f"      Role: {user.role}")
            print(f"      Active: {user.is_active}")
            print(f"      Hashed Password: {user.hashed_password[:50]}...")
        
        # Test password verification
        print(f"\n2. Testing password verification...")
        if user:
            try:
                is_valid = auth.verify_password(password, user.hashed_password)
                if is_valid:
                    print("   ✅ Password verification successful!")
                else:
                    print("   ❌ Password verification FAILED!")
                    print("   The stored password hash doesn't match.")
                    print("\n   Fixing by updating password...")
                    
                    # Update password
                    new_hash = auth.get_password_hash(password)
                    user.hashed_password = new_hash
                    db.commit()
                    db.refresh(user)
                    print("   ✅ Password updated successfully!")
                    
                    # Verify again
                    is_valid = auth.verify_password(password, user.hashed_password)
                    if is_valid:
                        print("   ✅ Password verification now works!")
                    else:
                        print("   ❌ Still failing - there may be a deeper issue")
            except Exception as e:
                print(f"   ❌ Error during verification: {e}")
                import traceback
                traceback.print_exc()
        
        # Test full authentication
        print(f"\n3. Testing full authentication...")
        authenticated_user = crud.authenticate_user(db, username, password)
        if authenticated_user:
            print("   ✅ Authentication successful!")
            print(f"      User ID: {authenticated_user.id}")
        else:
            print("   ❌ Authentication failed!")
        
        print("\n" + "=" * 60)
        print("Summary:")
        print("=" * 60)
        if authenticated_user:
            print("✅ User authentication is working!")
            print("\nYou can now use this command to get a token:")
            print(f"   curl -X POST 'http://127.0.0.1:8000/token' \\")
            print(f"     -H 'Content-Type: application/x-www-form-urlencoded' \\")
            print(f"     -d 'grant_type=password&username={username}&password={password}'")
        else:
            print("❌ User authentication is still not working.")
            print("   Please check the error messages above.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    diagnose_and_fix()
