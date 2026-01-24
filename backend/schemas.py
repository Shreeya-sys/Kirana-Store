from pydantic import BaseModel, field_validator
from typing import Optional

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    role: str = "staff"
    
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
