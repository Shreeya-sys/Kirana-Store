from pydantic import BaseModel, field_validator
from typing import Optional

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    role: str = "staff"  # root_admin, tenant_admin, staff, customer
    
    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        if not isinstance(v, str):
            v = str(v)
        
        # Check minimum length
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long.')
        
        # Note: No maximum length check needed anymore
        # We use SHA-256 pre-hashing which supports passwords of any length
        # The SHA-256 hash (64 hex chars = 32 bytes) is always < bcrypt's 72-byte limit
        
        return v

class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    tenant_id: Optional[str] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    role: Optional[str] = None  # User role for convenience

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class ItemBase(BaseModel):
    name: str
    sku: Optional[str] = None
    parent_unit: str
    child_unit: str
    conversion_factor: int

class ItemCreate(ItemBase):
    bulk_qty: int = 0
    loose_qty: int = 0

class ItemResponse(ItemBase):
    id: int
    bulk_qty: int
    loose_qty: int
    tenant_id: Optional[str] = None
    
    class Config:
        from_attributes = True

class InvoiceItemCreate(BaseModel):
    item_id: int
    quantity: int
    unit_price: int

class InvoiceCreate(BaseModel):
    customer_name: str
    customer_phone: str
    items: list[InvoiceItemCreate]
    status: str = "PAID"

class InvoiceResponse(BaseModel):
    id: int
    customer_name: str
    total_amount: int
    status: str
    timestamp: str
    
    class Config:
        from_attributes = True

class LedgerResponse(BaseModel):
    id: int
    customer_phone: str
    debit_amount: int
    credit_amount: int
    balance: int
    transaction_type: str
    timestamp: str

    class Config:
        from_attributes = True

# State Schemas
class StateBase(BaseModel):
    name: str  # e.g., "Maharashtra"
    code: str  # e.g., "MH" (2-letter code)
    gst_code: Optional[str] = None  # First 2 digits of GST number (e.g., "27" for Maharashtra)

class StateCreate(StateBase):
    pass

class StateResponse(StateBase):
    id: int
    is_active: bool
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True

# Shop and Owner Schemas
class ShopBase(BaseModel):
    shop_name: str
    password: Optional[str] = None  # Optional for admin-created stores; defaults are applied
    address: Optional[str] = None
    city: Optional[str] = None
    parent_shop_id: Optional[int] = None
    store_type: str = "main"  # main or branch
    state_id: Optional[int] = None  # Foreign key to State model
    state: Optional[str] = None  # Deprecated: kept for backward compatibility
    pincode: Optional[str] = None
    gst_number: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    email_password: Optional[str] = None  # Password for email account (will be encrypted)

class OwnerBase(BaseModel):
    owner_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    aadhaar_number: Optional[str] = None
    pan_number: Optional[str] = None
    address: Optional[str] = None

class ShopOnboardRequest(BaseModel):
    shop: ShopBase
    owner: OwnerBase

class ShopResponse(BaseModel):
    id: int
    shop_name: str
    shop_code: str
    api_key: str
    address: Optional[str] = None
    city: Optional[str] = None
    parent_shop_id: Optional[int] = None
    store_type: str = "main"
    state_id: Optional[int] = None  # Foreign key to State
    state: Optional[str] = None  # Deprecated: kept for backward compatibility
    state_name: Optional[str] = None  # State name from relationship
    state_code: Optional[str] = None  # State code from relationship
    pincode: Optional[str] = None
    gst_number: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: bool
    created_at: str
    # Note: password and email_password are not included in response for security

    class Config:
        from_attributes = True

class OwnerResponse(BaseModel):
    id: int
    shop_id: int
    owner_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    aadhaar_number: Optional[str] = None
    pan_number: Optional[str] = None
    address: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True

class ShopOnboardResponse(BaseModel):
    shop: ShopResponse
    owner: OwnerResponse
    shop_id: int  # Explicitly include shop_id for convenience
    message: str

class ShopAdminUpdate(BaseModel):
    shop_name: Optional[str] = None
    password: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    parent_shop_id: Optional[int] = None
    store_type: Optional[str] = None
    state_id: Optional[int] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    gst_number: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

# Customer Schemas
class CustomerBase(BaseModel):
    customer_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerResponse(CustomerBase):
    id: int
    shop_id: int
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True
