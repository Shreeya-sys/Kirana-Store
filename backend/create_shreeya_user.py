"""Quick script to create shreeya user"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
import crud
import schemas

db = SessionLocal()
try:
    # Check if user exists
    user = crud.get_user_by_username(db, username="shreeya")
    if user:
        print(f"User 'shreeya' already exists with role: {user.role}")
    else:
        # Create user
        user_data = schemas.UserCreate(
            username="shreeya",
            password="shreeya",
            role="root_admin"
        )
        user = crud.create_user(db, user_data)
        print(f"✅ User 'shreeya' created successfully!")
        print(f"   ID: {user.id}")
        print(f"   Username: {user.username}")
        print(f"   Role: {user.role}")
finally:
    db.close()
