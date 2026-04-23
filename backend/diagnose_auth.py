"""Diagnose authentication issues"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
import models
import crud
import auth

db = SessionLocal()
try:
    print("=" * 70)
    print("AUTHENTICATION DIAGNOSIS")
    print("=" * 70)
    
    username = "shreeya"
    password = "shreeya"
    
    # 1. Check if user exists
    print(f"\n1. Checking if user '{username}' exists...")
    user = crud.get_user_by_username(db, username=username)
    if not user:
        print(f"   ❌ User '{username}' does NOT exist in database!")
        print(f"   💡 Solution: Create the user first")
        print(f"\n   Creating user now...")
        try:
            import schemas
            user_data = schemas.UserCreate(
                username=username,
                password=password,
                role="root_admin"
            )
            user = crud.create_user(db, user_data)
            print(f"   ✅ User created successfully!")
            print(f"      ID: {user.id}")
            print(f"      Username: {user.username}")
            print(f"      Role: {user.role}")
        except Exception as e:
            print(f"   ❌ Failed to create user: {e}")
            import traceback
            traceback.print_exc()
            db.close()
            sys.exit(1)
    else:
        print(f"   ✅ User exists!")
        print(f"      ID: {user.id}")
        print(f"      Username: {user.username}")
        print(f"      Role: {user.role}")
        print(f"      Is Active: {user.is_active}")
    
    # 2. Check password hash
    print(f"\n2. Checking password hash...")
    if user.hashed_password:
        print(f"   Hash exists: {len(user.hashed_password)} characters")
        print(f"   Hash preview: {user.hashed_password[:60]}...")
    else:
        print(f"   ❌ No password hash stored!")
    
    # 3. Test password verification
    print(f"\n3. Testing password verification...")
    if user.hashed_password:
        try:
            is_valid = auth.verify_password(password, user.hashed_password)
            if is_valid:
                print(f"   ✅ Password verification SUCCESSFUL!")
            else:
                print(f"   ❌ Password verification FAILED!")
                print(f"   💡 The stored hash doesn't match the password")
                print(f"\n   Fixing by updating password hash...")
                new_hash = auth.get_password_hash(password)
                user.hashed_password = new_hash
                db.commit()
                db.refresh(user)
                print(f"   ✅ Password hash updated!")
                
                # Verify again
                is_valid = auth.verify_password(password, user.hashed_password)
                if is_valid:
                    print(f"   ✅ Password verification now works!")
                else:
                    print(f"   ❌ Still failing - there may be a deeper issue")
        except Exception as e:
            print(f"   ❌ Error during verification: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"   ❌ Cannot verify - no password hash")
    
    # 4. Test full authentication
    print(f"\n4. Testing full authentication flow...")
    authenticated_user = crud.authenticate_user(db, username, password)
    if authenticated_user:
        print(f"   ✅ Authentication SUCCESSFUL!")
        print(f"      User ID: {authenticated_user.id}")
        print(f"      Username: {authenticated_user.username}")
        print(f"      Role: {authenticated_user.role}")
    else:
        print(f"   ❌ Authentication FAILED!")
        print(f"   💡 Check the errors above")
    
    # 5. Check shops and their users
    print(f"\n5. Checking shops and linked users...")
    shops = db.query(models.Shop).all()
    print(f"   Total shops: {len(shops)}")
    for shop in shops:
        print(f"\n   Shop: {shop.shop_name} (code: {shop.shop_code})")
        linked_user = db.query(models.User).filter(models.User.shop_id == shop.id).first()
        if linked_user:
            print(f"      Linked User: {linked_user.username} (role: {linked_user.role})")
            # Test if user can login with shop password
            test_pwd = "test"  # We don't know the actual shop password
            print(f"      ⚠️  Cannot test - shop password unknown")
        else:
            print(f"      ⚠️  No linked user found!")
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    if authenticated_user:
        print("✅ Authentication is working!")
        print(f"\nYou can now login with:")
        print(f"  curl -X POST 'http://127.0.0.1:8000/token' \\")
        print(f"    -H 'Content-Type: application/x-www-form-urlencoded' \\")
        print(f"    -d 'username={username}&password={password}'")
    else:
        print("❌ Authentication is NOT working!")
        print("   Please check the errors above.")
    
finally:
    db.close()
