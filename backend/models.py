from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import secrets
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(Text)  # Changed to Text for future-proofing (bcrypt hashes are 60 chars, but allows for algorithm changes)
    role = Column(String, default="staff") # root_admin, tenant_admin, staff, customer
    tenant_id = Column(String, index=True, nullable=True) # For multi-tenancy later (deprecated, use shop_id)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)  # Link to shop
    is_active = Column(Boolean, default=True)
    
    # Relationships
    shop = relationship("Shop", back_populates="users")

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    sku = Column(String, index=True, nullable=True)
    
    # Dual-Unit Logic
    parent_unit = Column(String) # e.g., "Sack"
    child_unit = Column(String) # e.g., "Gram"
    conversion_factor = Column(Integer) # e.g., 10000 (1 Sack = 10000 Grams)
    
    # Inventory Snapshots
    bulk_qty = Column(Integer, default=0) # Number of Parent Units
    loose_qty = Column(Integer, default=0) # Number of Child Units
    
    # Multi-tenancy
    tenant_id = Column(String, index=True, nullable=True) # Deprecated, use shop_id
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)  # Link to shop
    
    # Relationships
    shop = relationship("Shop", back_populates="items")

class StockAdjustment(Base):
    __tablename__ = "stock_adjustments"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, index=True)
    adjustment_type = Column(String) # "DECANT", "SALE", "PURCHASE", "WASTAGE"
    quantity_change_bulk = Column(Integer, default=0)
    quantity_change_loose = Column(Integer, default=0)
    timestamp = Column(String) # Store isoformat datetime
    tenant_id = Column(String, index=True, nullable=True) # Deprecated, use shop_id
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)  # Link to shop

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String, index=True) # CREATE, UPDATE, DELETE
    table_name = Column(String)
    timestamp = Column(String)
    tenant_id = Column(String, index=True, nullable=True)

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, index=True)
    customer_phone = Column(String, index=True)
    total_amount = Column(Integer) # In cents/paisa? Let's use Float or Integer. Using Float for simplicity now.
    tax_amount = Column(Integer)
    status = Column(String, default="PAID") # PAID, CREDIT
    timestamp = Column(String)
    tenant_id = Column(String, index=True, nullable=True) # Deprecated, use shop_id
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)  # Link to shop
    
    # Relationships
    shop = relationship("Shop", back_populates="invoices")

class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, index=True)
    item_id = Column(Integer)
    quantity = Column(Integer)
    unit_price = Column(Integer)
    total_price = Column(Integer)
    tenant_id = Column(String, index=True, nullable=True) # Deprecated, use shop_id
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)  # Link to shop

class Ledger(Base):
    __tablename__ = "ledgers"

    id = Column(Integer, primary_key=True, index=True)
    customer_phone = Column(String, index=True) # Link to invoice customer
    debit_amount = Column(Integer, default=0) # Udhaar taken
    credit_amount = Column(Integer, default=0) # Udhaar paid
    balance = Column(Integer, default=0) # Net outstanding
    transaction_type = Column(String) # INVOICE, PAYMENT
    reference_id = Column(String) # Invoice ID or Payment Ref
    timestamp = Column(String)
    tenant_id = Column(String, index=True, nullable=True) # Deprecated, use shop_id
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)  # Link to shop

class State(Base):
    __tablename__ = "states"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)  # e.g., "Maharashtra"
    code = Column(String, unique=True, index=True, nullable=False)  # e.g., "MH" (2-letter code)
    gst_code = Column(String, nullable=True)  # First 2 digits of GST number (e.g., "27" for Maharashtra)
    is_active = Column(Boolean, default=True)
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())
    updated_at = Column(String, default=lambda: datetime.utcnow().isoformat())
    
    # Relationships
    shops = relationship("Shop", back_populates="state_rel")

class Shop(Base):
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True, index=True)
    shop_name = Column(String, index=True, nullable=False)
    shop_code = Column(String, unique=True, index=True, nullable=False)  # Unique identifier for shop
    api_key = Column(String, unique=True, index=True, nullable=False)  # API key for authentication
    hashed_password = Column(Text, nullable=False)  # Password for shop authentication
    address = Column(Text, nullable=True)
    city = Column(String, nullable=True)
    state_id = Column(Integer, ForeignKey("states.id"), nullable=True, index=True)  # Foreign key to State
    state = Column(String, nullable=True)  # Deprecated: kept for backward compatibility during migration
    pincode = Column(String, nullable=True)
    gst_number = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    email_password = Column(Text, nullable=True)  # Encrypted password for email account
    is_active = Column(Boolean, default=True)
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())
    updated_at = Column(String, default=lambda: datetime.utcnow().isoformat())
    
    # Relationships
    state_rel = relationship("State", back_populates="shops")
    owner = relationship("Owner", back_populates="shop", uselist=False)
    users = relationship("User", back_populates="shop")
    customers = relationship("Customer", back_populates="shop")
    items = relationship("Item", back_populates="shop")
    invoices = relationship("Invoice", back_populates="shop")

class Owner(Base):
    __tablename__ = "owners"

    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, unique=True)
    owner_name = Column(String, nullable=False)
    phone = Column(String, index=True, nullable=True)
    email = Column(String, nullable=True)
    aadhaar_number = Column(String, nullable=True)
    pan_number = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())
    updated_at = Column(String, default=lambda: datetime.utcnow().isoformat())
    
    # Relationships
    shop = relationship("Shop", back_populates="owner")

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, index=True)  # Link to shop/tenant
    customer_name = Column(String, nullable=False, index=True)
    phone = Column(String, index=True, nullable=True)
    email = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())
    updated_at = Column(String, default=lambda: datetime.utcnow().isoformat())
    
    # Relationships
    shop = relationship("Shop", back_populates="customers")
