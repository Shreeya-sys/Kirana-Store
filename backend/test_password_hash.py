"""Test password hashing and verification"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import auth

# Test the hashing logic
password = "shreeya"
print("=" * 70)
print("PASSWORD HASHING TEST")
print("=" * 70)
print(f"Password: '{password}'")
print(f"Password length: {len(password)} bytes")

# Hash the password
try:
    hash1 = auth.get_password_hash(password)
    print(f"\n✅ Hash created successfully!")
    print(f"Hash (first 60 chars): {hash1[:60]}...")
    print(f"Hash length: {len(hash1)} characters")
    
    # Verify the password
    is_valid = auth.verify_password(password, hash1)
    print(f"\nVerification result: {'✅ VALID' if is_valid else '❌ INVALID'}")
    
    # Test with different hash (should still verify)
    hash2 = auth.get_password_hash(password)
    print(f"\nHash 2 (first 60 chars): {hash2[:60]}...")
    is_valid2 = auth.verify_password(password, hash2)
    print(f"Verification with hash2: {'✅ VALID' if is_valid2 else '❌ INVALID'}")
    
    if hash1 == hash2:
        print("⚠️  WARNING: Hashes are identical (unusual - should be different due to salt)")
    else:
        print("✅ Hashes are different (expected - bcrypt uses random salt)")
    
    # Test wrong password
    wrong_pwd = "wrongpassword"
    is_wrong = auth.verify_password(wrong_pwd, hash1)
    print(f"\nWrong password test: {'❌ FAILED (correct)' if not is_wrong else '⚠️  PASSED (unexpected!)'}")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
