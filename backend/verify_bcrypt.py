from passlib.context import CryptContext
import sys

try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hash_ = pwd_context.hash("testpassword")
    print(f"Successfully hashed password: {hash_[:10]}...")
    print("verification_success")
except Exception as e:
    print(f"Verification failed: {e}")
    sys.exit(1)
