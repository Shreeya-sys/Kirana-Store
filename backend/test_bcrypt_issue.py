#!/usr/bin/env python3
"""
Test script to diagnose bcrypt password hashing issue
"""

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Test with the exact password from the user
test_password = "shreeya"
password_bytes = test_password.encode('utf-8')
password_length = len(password_bytes)

print(f"Testing password: '{test_password}'")
print(f"Character length: {len(test_password)}")
print(f"Byte length: {password_length}")
print(f"Should be valid: {password_length <= 72}")

try:
    print("\nAttempting to hash password...")
    hashed = pwd_context.hash(test_password)
    print(f"✅ SUCCESS! Hash: {hashed[:20]}...")
    
    # Test verification
    print("\nTesting verification...")
    is_valid = pwd_context.verify(test_password, hashed)
    print(f"✅ Verification: {is_valid}")
    
except ValueError as e:
    print(f"\n❌ ValueError: {e}")
    print(f"Error type: {type(e)}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    print(f"Error type: {type(e)}")
    import traceback
    traceback.print_exc()
