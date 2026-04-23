"""
Script to create a user for testing.

Run from project root:  python backend\\create_user.py
Or from backend folder:  python create_user.py
"""
import sys
import os

# Run from script directory so it works from project root or backend
_script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(_script_dir)
sys.path.insert(0, _script_dir)

from database import SessionLocal
import crud
import schemas

def create_test_user():
    """Create a test user"""
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = crud.get_user_by_username(db, username="shreeya")
        if existing_user:
            print("[SKIP] User 'shreeya' already exists!")
            print(f"   User ID: {existing_user.id}")
            print(f"   Role: {existing_user.role}")
            print(f"   Active: {existing_user.is_active}")
            return

        # Create new user (root_admin so they can use POST /states and other admin APIs)
        user_data = schemas.UserCreate(
            username="shreeya",
            password="shreeya",
            role="root_admin"
        )

        user = crud.create_user(db, user_data)
        print("[OK] User created successfully!")
        print(f"   Username: {user.username}")
        print(f"   Role: {user.role}")
        print(f"   ID: {user.id}")
        print("\nTip: Get a token then call POST /states, etc.:")
        print("   Invoke-RestMethod -Uri 'http://127.0.0.1:8000/token' -Method Post -Body @{username='shreeya';password='shreeya'} -ContentType 'application/x-www-form-urlencoded'")

    except Exception as e:
        print(f"[ERROR] Error creating user: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()
