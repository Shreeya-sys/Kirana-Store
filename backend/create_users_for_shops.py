"""
Script to create user accounts for existing shops
This fixes the issue where shops were onboarded but no user account was created
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
import crud
import schemas
import models

def create_users_for_existing_shops():
    """Create user accounts for shops that don't have linked users"""
    db = SessionLocal()
    try:
        print("=" * 60)
        print("Creating User Accounts for Existing Shops")
        print("=" * 60)
        
        # Get all shops
        shops = db.query(models.Shop).all()
        print(f"\nFound {len(shops)} shops in database")
        
        created_count = 0
        skipped_count = 0
        
        for shop in shops:
            # Check if user with shop_code already exists
            existing_user = crud.get_user_by_username(db, username=shop.shop_code)
            
            if existing_user:
                print(f"\n⏭️  Shop '{shop.shop_name}' (code: {shop.shop_code})")
                print(f"   User account already exists: {existing_user.username}")
                skipped_count += 1
                continue
            
            # Check if we can get the password (we can't, it's hashed)
            # So we'll need to set a default password or ask user to reset
            # For now, let's use a default that they should change
            default_password = "changeme123"  # Users should change this
            
            try:
                # Create user account
                user_data = schemas.UserCreate(
                    username=shop.shop_code,
                    password=default_password,  # Default password - user should change
                    role="admin"
                )
                db_user = crud.create_user(db, user_data)
                
                # Link user to shop
                db_user.shop_id = shop.id
                db.commit()
                db.refresh(db_user)
                
                print(f"\n✅ Created user account for shop '{shop.shop_name}'")
                print(f"   Shop Code: {shop.shop_code}")
                print(f"   Username: {db_user.username}")
                print(f"   Default Password: {default_password} (⚠️  Please change this!)")
                print(f"   Role: {db_user.role}")
                created_count += 1
                
            except Exception as e:
                print(f"\n❌ Failed to create user for shop '{shop.shop_name}': {e}")
                db.rollback()
        
        print("\n" + "=" * 60)
        print("Summary:")
        print("=" * 60)
        print(f"✅ Created: {created_count} user accounts")
        print(f"⏭️  Skipped: {skipped_count} (already exist)")
        print(f"\n💡 To login with these accounts:")
        print(f"   Username: <shop_code>")
        print(f"   Password: changeme123 (change this after first login!)")
        print(f"\n   Example:")
        print(f"   curl -X POST 'http://127.0.0.1:8000/token' \\")
        print(f"     -H 'Content-Type: application/x-www-form-urlencoded' \\")
        print(f"     -d 'grant_type=password&username=<shop_code>&password=changeme123'")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_users_for_existing_shops()
