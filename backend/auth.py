from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Header, Security
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlalchemy.orm import Session
import hashlib
import bcrypt
import secrets
import schemas, models, database, crud

# SECRET_KEY should be in env/config for prod, hardcoded for task
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def generate_api_key() -> str:
    """Generate a secure random API key"""
    return f"kf_{secrets.token_urlsafe(32)}"

def generate_shop_code(shop_name: str) -> str:
    """Generate a unique shop code from shop name"""
    # Convert to uppercase, remove spaces, take first 6 chars
    base_code = shop_name.upper().replace(" ", "")[:6]
    # Add random suffix for uniqueness
    suffix = secrets.token_hex(2).upper()
    return f"{base_code}{suffix}"

def get_shop_by_api_key(db: Session, api_key: str) -> Optional[models.Shop]:
    """Get shop by API key"""
    return db.query(models.Shop).filter(models.Shop.api_key == api_key, models.Shop.is_active == True).first()

def get_shop_by_code(db: Session, shop_code: str) -> Optional[models.Shop]:
    """Get shop by shop_code"""
    return db.query(models.Shop).filter(models.Shop.shop_code == shop_code, models.Shop.is_active == True).first()

def authenticate_shop(db: Session, shop_code: str, password: str) -> Optional[models.Shop]:
    """Authenticate shop using shop_code and password"""
    shop = get_shop_by_code(db, shop_code)
    if not shop:
        return None
    if not verify_password(password, shop.hashed_password):
        return None
    return shop

def get_db():
    """Database dependency for auth functions"""
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_api_key(api_key: Optional[str] = Header(None, alias="X-API-Key"), db: Session = Depends(get_db)) -> models.Shop:
    """Verify API key and return shop"""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Please provide X-API-Key header."
        )
    
    shop = get_shop_by_api_key(db, api_key)
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key"
        )
    return shop

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

def get_current_user_optional(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(database.SessionLocal)) -> Optional[models.User]:
    """Get current user if authenticated, otherwise return None (for optional auth endpoints)"""
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        user = crud.get_user_by_username(db, username=username)
        return user if user and user.is_active else None
    except (JWTError, Exception):
        return None

# Role-based access control functions
def require_root_admin(current_user: models.User = Depends(get_current_active_user)):
    """Require root_admin role - can manage all tenants"""
    if current_user.role != "root_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Root admin access required"
        )
    return current_user

def require_tenant_admin(current_user: models.User = Depends(get_current_active_user)):
    """Require tenant_admin role - can manage their own shop"""
    if current_user.role != "tenant_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant admin access required"
        )
    if not current_user.shop_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not linked to a shop"
        )
    return current_user

def require_tenant_admin_or_staff(current_user: models.User = Depends(get_current_active_user)):
    """Require tenant_admin or staff role - can access shop resources"""
    if current_user.role not in ["tenant_admin", "staff"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant admin or staff access required"
        )
    if not current_user.shop_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not linked to a shop"
        )
    return current_user
