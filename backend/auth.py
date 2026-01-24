from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import hashlib
import bcrypt
import schemas, models, database, crud

# SECRET_KEY should be in env/config for prod, hardcoded for task
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_password_hash(password):
    """
    Hash password using SHA-256 pre-hashing + bcrypt.
    This allows passwords of any length while avoiding bcrypt's 72-byte limit.
    """
    if not isinstance(password, str):
        password = str(password)
    
    # Pre-hash with SHA-256 to remove bcrypt's 72-byte limit
    # SHA-256 produces 64 hex characters (32 bytes), which is always < 72 bytes
    sha256_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    try:
        # Hash the SHA-256 hash with bcrypt (always 64 bytes < 72)
        # Use bcrypt directly to avoid passlib compatibility issues
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(sha256_hash.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password hashing error: {str(e)}"
        )

def verify_password(plain_password, hashed_password):
    """
    Verify password by pre-hashing with SHA-256, then verifying with bcrypt.
    """
    # Pre-hash the plain password with SHA-256 (same as in get_password_hash)
    sha256_hash = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
    # Verify the SHA-256 hash against the bcrypt hash using bcrypt directly
    return bcrypt.checkpw(sha256_hash.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.SessionLocal)): # Adjusted dependency for simplicity in this context, ideally use get_db
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username, role=payload.get("role"))
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
