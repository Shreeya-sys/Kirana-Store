"""Script to check database users and verify password hashing"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
import models
import auth

db = SessionLocal()
try:
    print("=" * 80)
    print("DATABASE USER INSPECTION")
    print("=" * 80)
    
    # Get all users
    users = db.query(models.User).all()
    print(f"\n📊 Total Users in Database: {len(users)}\n")
    
    if not users:
        print("❌ No users found in database!")
    else:
        for user in users:
            print(f"User ID: {user.id}")
            print(f"  Username: {user.username}")
            print(f"  Role: {user.role}")
            print(f"  Shop ID: {user.shop_id}")
            print(f"  Is Active: {user.is_active}")
            print(f"  Hashed Password (first 50 chars): {user.hashed_password[:50] if user.hashed_password else 'None'}...")
            print(f"  Hashed Password Length: {len(user.hashed_password) if user.hashed_password else 0}")
            
            # Test password verification
            if user.username == "shreeya":
                print(f"\n  🔍 Testing password verification for 'shreeya':")
                test_password = "shreeya"
                is_valid = auth.verify_password(test_password, user.hashed_password)
                print(f"    Password 'shreeya' verification: {'✅ VALID' if is_valid else '❌ INVALID'}")
            
            # If user is linked to a shop, check shop password
            if user.shop_id:
                shop = db.query(models.Shop).filter(models.Shop.id == user.shop_id).first()
                if shop:
                    print(f"  📦 Linked Shop: {shop.shop_name} (code: {shop.shop_code})")
                    print(f"    Shop Hashed Password (first 50 chars): {shop.hashed_password[:50] if shop.hashed_password else 'None'}...")
                    print(f"    Shop Hashed Password Length: {len(shop.hashed_password) if shop.hashed_password else 0}")
                    
                    # Check if user password hash matches shop password hash
                    if user.hashed_password and shop.hashed_password:
                        if user.hashed_password == shop.hashed_password:
                            print(f"    ⚠️  WARNING: User password hash MATCHES shop password hash!")
                            print(f"       This is expected if they use the same password.")
                        else:
                            print(f"    ℹ️  User and shop have different password hashes (expected if different passwords)")
            
            print("-" * 80)
    
    # Check shops
    print("\n" + "=" * 80)
    print("SHOPS IN DATABASE")
    print("=" * 80)
    shops = db.query(models.Shop).all()
    print(f"\n📊 Total Shops: {len(shops)}\n")
    
    for shop in shops:
        print(f"Shop ID: {shop.id}")
        print(f"  Shop Name: {shop.shop_name}")
        print(f"  Shop Code: {shop.shop_code}")
        print(f"  Hashed Password (first 50 chars): {shop.hashed_password[:50] if shop.hashed_password else 'None'}...")
        print(f"  Hashed Password Length: {len(shop.hashed_password) if shop.hashed_password else 0}")
        
        # Find linked user
        linked_user = db.query(models.User).filter(models.User.shop_id == shop.id).first()
        if linked_user:
            print(f"  👤 Linked User: {linked_user.username} (role: {linked_user.role})")
            print(f"    User Hashed Password (first 50 chars): {linked_user.hashed_password[:50] if linked_user.hashed_password else 'None'}...")
            print(f"    User Hashed Password Length: {len(linked_user.hashed_password) if linked_user.hashed_password else 0}")
            
            # Test if passwords match (they should if created during onboarding)
            if linked_user.hashed_password and shop.hashed_password:
                if linked_user.hashed_password == shop.hashed_password:
                    print(f"    ✅ User and shop password hashes MATCH (same password)")
                else:
                    print(f"    ⚠️  User and shop password hashes DIFFER (different passwords)")
        else:
            print(f"  ⚠️  No linked user found!")
        print("-" * 80)
    
    print("\n" + "=" * 80)
    print("PASSWORD HASHING TEST")
    print("=" * 80)
    test_password = "test123"
    print(f"\nTesting with password: '{test_password}'")
    hash1 = auth.get_password_hash(test_password)
    print(f"Hash 1 (first 50 chars): {hash1[:50]}...")
    print(f"Hash 1 Length: {len(hash1)}")
    
    # Generate another hash (should be different due to salt)
    hash2 = auth.get_password_hash(test_password)
    print(f"Hash 2 (first 50 chars): {hash2[:50]}...")
    print(f"Hash 2 Length: {len(hash2)}")
    
    if hash1 == hash2:
        print("⚠️  WARNING: Two hashes of same password are identical (should be different due to salt)")
    else:
        print("✅ Hashes are different (expected - bcrypt uses random salt)")
    
    # Verify both hashes
    verify1 = auth.verify_password(test_password, hash1)
    verify2 = auth.verify_password(test_password, hash2)
    print(f"\nVerification Test:")
    print(f"  Hash 1 verification: {'✅ VALID' if verify1 else '❌ INVALID'}")
    print(f"  Hash 2 verification: {'✅ VALID' if verify2 else '❌ INVALID'}")
    
finally:
    db.close()
