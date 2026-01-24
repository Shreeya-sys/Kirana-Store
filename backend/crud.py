from sqlalchemy.orm import Session
from datetime import datetime
import models, schemas, auth

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    try:
        hashed_password = auth.get_password_hash(user.password)
    except Exception as e:
        # Re-raise HTTPException as-is, convert others to HTTPException
        from fastapi import HTTPException, status
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password validation failed: {str(e)}"
        )
    
    db_user = models.User(username=user.username, hashed_password=hashed_password, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not auth.verify_password(password, user.hashed_password):
        return False
    return user

def create_item(db: Session, item: schemas.ItemCreate):
    db_item = models.Item(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()

def decant_stock(db: Session, item_id: int):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item or item.bulk_qty < 1:
        return None
    
    # Logic: -1 Bulk, +Conversion Loose
    item.bulk_qty -= 1
    item.loose_qty += item.conversion_factor
    
    # Log Adjustment
    adj = models.StockAdjustment(
        item_id=item_id,
        adjustment_type="DECANT",
        quantity_change_bulk=-1,
        quantity_change_loose=item.conversion_factor,
        timestamp=datetime.utcnow().isoformat()
    )
    db.add(adj)
    db.commit()
    db.refresh(item)
    return item

def create_invoice(db: Session, invoice: schemas.InvoiceCreate):
    total = 0
    # 1. Calculate Total & Verify Stock
    for item_in in invoice.items:
        # Simplified: Check stock and calculate price
        total += item_in.quantity * item_in.unit_price
        # Note: Ideally, check Item stock here and deduct.
        # Deducting loose_qty for simplicity
        db_item = db.query(models.Item).filter(models.Item.id == item_in.item_id).first()
        if db_item:
            db_item.loose_qty -= item_in.quantity
    
    # 2. Create Invoice
    db_invoice = models.Invoice(
        customer_name=invoice.customer_name,
        customer_phone=invoice.customer_phone,
        total_amount=total,
        tax_amount=0, # Simplified
        status=invoice.status,
        timestamp=datetime.utcnow().isoformat()
    )
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    
    # 3. Create Invoice Items
    for item_in in invoice.items:
        db_inv_item = models.InvoiceItem(
            invoice_id=db_invoice.id,
            item_id=item_in.item_id,
            quantity=item_in.quantity,
            unit_price=item_in.unit_price,
            total_price=item_in.quantity * item_in.unit_price
        )
        db.add(db_inv_item)
    
    # 4. Update Ledger if Credit
    if invoice.status == "CREDIT":
        # Get last balance
        last_entry = db.query(models.Ledger).filter(models.Ledger.customer_phone == invoice.customer_phone).order_by(models.Ledger.id.desc()).first()
        prev_balance = last_entry.balance if last_entry else 0
        new_balance = prev_balance + total # Adding debt
        
        ledger_entry = models.Ledger(
            customer_phone=invoice.customer_phone,
            debit_amount=total,
            credit_amount=0,
            balance=new_balance,
            transaction_type="INVOICE",
            reference_id=str(db_invoice.id),
            timestamp=datetime.utcnow().isoformat()
        )
        db.add(ledger_entry)

    db.commit()
    return db_invoice

def get_ledger(db: Session, phone: str):
    return db.query(models.Ledger).filter(models.Ledger.customer_phone == phone).all()
