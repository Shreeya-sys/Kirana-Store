"""Inspect database users and shops"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
import models
import auth

db = SessionLocal()
try:
    print("=" * 70)
    print("USERS IN DATABASE")
    print("=" * 70)
    users = db.query(models.User).all()
    print(f"Total: {len(users)}\n")
    
    for u in users:
        print(f"ID: {u.id}, Username: {u.username}, Role: {u.role}, Shop ID: {u.shop_id}")
        if u.hashed_password:
            print(f"  Password Hash: {u.hashed_password[:60]}... (len: {len(u.hashed_password)})")
        if u.username == "shreeya":
            test_pwd = "shreeya"
            valid = auth.verify_password(test_pwd, u.hashed_password) if u.hashed_password else False
            print(f"  Verify 'shreeya': {'✅' if valid else '❌'}")
        print()
    
    print("=" * 70)
    print("SHOPS IN DATABASE")
    print("=" * 70)
    shops = db.query(models.Shop).all()
    print(f"Total: {len(shops)}\n")
    
    for s in shops:
        print(f"ID: {s.id}, Name: {s.shop_name}, Code: {s.shop_code}")
        if s.hashed_password:
            print(f"  Shop Password Hash: {s.hashed_password[:60]}... (len: {len(s.hashed_password)})")
        
        # Find linked user
        user = db.query(models.User).filter(models.User.shop_id == s.id).first()
        if user:
            print(f"  Linked User: {user.username} (role: {user.role})")
            if user.hashed_password:
                print(f"  User Password Hash: {user.hashed_password[:60]}... (len: {len(user.hashed_password)})")
                # Check if hashes match (they shouldn't - different salts)
                if s.hashed_password == user.hashed_password:
                    print(f"  ⚠️  Hashes MATCH (unusual - same salt)")
                else:
                    print(f"  ✅ Hashes differ (expected - different salts)")
        print()
    
    print("=" * 70)
    print("PASSWORD HASHING TEST")
    print("=" * 70)
    pwd = "test123"
    h1 = auth.get_password_hash(pwd)
    h2 = auth.get_password_hash(pwd)
    print(f"Password: '{pwd}'")
    print(f"Hash 1: {h1[:60]}...")
    print(f"Hash 2: {h2[:60]}...")
    print(f"Same? {h1 == h2} (should be False - different salts)")
    print(f"Verify 1: {auth.verify_password(pwd, h1)}")
    print(f"Verify 2: {auth.verify_password(pwd, h2)}")
    
finally:
    db.close()
