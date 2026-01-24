from sqlalchemy import Column, Integer, String, Boolean, Text
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(Text)  # Changed to Text for future-proofing (bcrypt hashes are 60 chars, but allows for algorithm changes)
    role = Column(String, default="staff") # admin, staff
    tenant_id = Column(String, index=True, nullable=True) # For multi-tenancy later
    is_active = Column(Boolean, default=True)

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
    
    tenant_id = Column(String, index=True, nullable=True)

class StockAdjustment(Base):
    __tablename__ = "stock_adjustments"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, index=True)
    adjustment_type = Column(String) # "DECANT", "SALE", "PURCHASE", "WASTAGE"
    quantity_change_bulk = Column(Integer, default=0)
    quantity_change_loose = Column(Integer, default=0)
    timestamp = Column(String) # Store isoformat datetime
    tenant_id = Column(String, index=True, nullable=True)

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
    tenant_id = Column(String, index=True, nullable=True)

class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, index=True)
    item_id = Column(Integer)
    quantity = Column(Integer)
    unit_price = Column(Integer)
    total_price = Column(Integer)
    tenant_id = Column(String, index=True, nullable=True)

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
    tenant_id = Column(String, index=True, nullable=True)
