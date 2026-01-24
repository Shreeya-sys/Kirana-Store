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

def create_item(db: Session, item: schemas.ItemCreate, shop_id: int = None):
    db_item = models.Item(**item.dict())
    if shop_id:
        db_item.shop_id = shop_id
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_items(db: Session, skip: int = 0, limit: int = 100, shop_id: int = None):
    query = db.query(models.Item)
    if shop_id:
        query = query.filter(models.Item.shop_id == shop_id)
    return query.offset(skip).limit(limit).all()

def get_items_by_shop(db: Session, shop_id: int, skip: int = 0, limit: int = 100):
    """Get all items for a shop"""
    return db.query(models.Item).filter(
        models.Item.shop_id == shop_id
    ).offset(skip).limit(limit).all()

def decant_stock(db: Session, item_id: int, shop_id: int = None):
    query = db.query(models.Item).filter(models.Item.id == item_id)
    if shop_id:
        query = query.filter(models.Item.shop_id == shop_id)
    item = query.first()
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
        timestamp=datetime.utcnow().isoformat(),
        shop_id=shop_id
    )
    db.add(adj)
    db.commit()
    db.refresh(item)
    return item

def create_invoice(db: Session, invoice: schemas.InvoiceCreate, shop_id: int = None):
    total = 0
    # 1. Calculate Total & Verify Stock
    query = db.query(models.Item)
    if shop_id:
        query = query.filter(models.Item.shop_id == shop_id)
    
    for item_in in invoice.items:
        # Simplified: Check stock and calculate price
        total += item_in.quantity * item_in.unit_price
        # Note: Ideally, check Item stock here and deduct.
        # Deducting loose_qty for simplicity
        db_item = query.filter(models.Item.id == item_in.item_id).first()
        if db_item:
            db_item.loose_qty -= item_in.quantity
    
    # 2. Create Invoice
    db_invoice = models.Invoice(
        customer_name=invoice.customer_name,
        customer_phone=invoice.customer_phone,
        total_amount=total,
        tax_amount=0, # Simplified
        status=invoice.status,
        timestamp=datetime.utcnow().isoformat(),
        shop_id=shop_id
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
            total_price=item_in.quantity * item_in.unit_price,
            shop_id=shop_id
        )
        db.add(db_inv_item)
    
    # 4. Update Ledger if Credit
    if invoice.status == "CREDIT":
        # Get last balance (filtered by shop_id)
        ledger_query = db.query(models.Ledger).filter(models.Ledger.customer_phone == invoice.customer_phone)
        if shop_id:
            ledger_query = ledger_query.filter(models.Ledger.shop_id == shop_id)
        last_entry = ledger_query.order_by(models.Ledger.id.desc()).first()
        prev_balance = last_entry.balance if last_entry else 0
        new_balance = prev_balance + total # Adding debt
        
        ledger_entry = models.Ledger(
            customer_phone=invoice.customer_phone,
            debit_amount=total,
            credit_amount=0,
            balance=new_balance,
            transaction_type="INVOICE",
            reference_id=str(db_invoice.id),
            timestamp=datetime.utcnow().isoformat(),
            shop_id=shop_id
        )
        db.add(ledger_entry)

    db.commit()
    return db_invoice

def get_ledger(db: Session, phone: str, shop_id: int = None):
    query = db.query(models.Ledger).filter(models.Ledger.customer_phone == phone)
    if shop_id:
        query = query.filter(models.Ledger.shop_id == shop_id)
    return query.all()

# Shop and Owner CRUD operations
def create_shop_with_owner(db: Session, shop_data: schemas.ShopBase, owner_data: schemas.OwnerBase):
    """Create a shop with owner - onboarding"""
    from fastapi import HTTPException, status
    import auth
    
    # Validate password length
    if len(shop_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )
    
    # Hash the password
    try:
        hashed_password = auth.get_password_hash(shop_data.password)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password hashing failed: {str(e)}"
        )
    
    # Generate unique shop_code and api_key
    shop_code = auth.generate_shop_code(shop_data.shop_name)
    api_key = auth.generate_api_key()
    
    # Check if shop_code already exists (unlikely but possible)
    existing_shop = db.query(models.Shop).filter(models.Shop.shop_code == shop_code).first()
    if existing_shop:
        # Regenerate if collision
        shop_code = auth.generate_shop_code(shop_data.shop_name + str(datetime.utcnow().timestamp()))
    
    # Encrypt email password if provided
    encrypted_email_password = None
    if shop_data.email_password:
        try:
            # Encrypt email password using the same hashing method as shop password
            encrypted_email_password = auth.get_password_hash(shop_data.email_password)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email password encryption failed: {str(e)}"
            )
    
    # Handle state_id or state (backward compatibility)
    state_id = shop_data.state_id
    state_name = shop_data.state  # Deprecated field
    
    # If state_id is 0 or None, treat it as None (invalid foreign key)
    if state_id == 0:
        state_id = None
    
    # Validate state_id if provided (must exist in database)
    if state_id is not None:
        state_obj = db.query(models.State).filter(models.State.id == state_id).first()
        if not state_obj:
            # Invalid state_id provided - set to None to avoid foreign key error
            state_id = None
            # Try to find by state name if provided
            if state_name:
                state_obj = db.query(models.State).filter(models.State.name == state_name).first()
                if not state_obj:
                    state_obj = db.query(models.State).filter(models.State.code == state_name).first()
                if state_obj:
                    state_id = state_obj.id
    
    # If state_id is still not provided but state name is, try to find state by name
    if not state_id and state_name:
        # Query state by name directly
        state_obj = db.query(models.State).filter(models.State.name == state_name).first()
        if not state_obj:
            # Try by code
            state_obj = db.query(models.State).filter(models.State.code == state_name).first()
        if state_obj:
            state_id = state_obj.id
    
    # Create shop
    db_shop = models.Shop(
        shop_name=shop_data.shop_name,
        shop_code=shop_code,
        api_key=api_key,
        hashed_password=hashed_password,
        address=shop_data.address,
        city=shop_data.city,
        state_id=state_id,
        state=state_name,  # Keep for backward compatibility
        pincode=shop_data.pincode,
        gst_number=shop_data.gst_number,
        phone=shop_data.phone,
        email=shop_data.email,
        email_password=encrypted_email_password,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat()
    )
    db.add(db_shop)
    db.flush()  # Flush to get shop.id
    
    # Create owner
    db_owner = models.Owner(
        shop_id=db_shop.id,
        owner_name=owner_data.owner_name,
        phone=owner_data.phone,
        email=owner_data.email,
        aadhaar_number=owner_data.aadhaar_number,
        pan_number=owner_data.pan_number,
        address=owner_data.address,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat()
    )
    db.add(db_owner)
    
    # CRITICAL: Automatically create a user account for seamless login integration
    # This is a fundamental requirement - shop onboarding MUST create a user account
    # Use shop_code as username and shop password for unified authentication
    db_user = None
    try:
        # Check if user with shop_code already exists
        existing_user = get_user_by_username(db, username=shop_code)
        if existing_user:
            # User already exists - link it to this shop if not already linked
            if not existing_user.shop_id:
                existing_user.shop_id = db_shop.id
                db.add(existing_user)
        else:
            # Create user account linked to the shop
            # This allows immediate login via /token endpoint after onboarding
            user_data = schemas.UserCreate(
                username=shop_code,
                password=shop_data.password,  # Same password as shop for unified auth
                role="tenant_admin"  # Shop owner gets tenant_admin role (manages their shop)
            )
            db_user = create_user(db, user_data)
            # Link user to shop
            db_user.shop_id = db_shop.id
            db.add(db_user)
    except Exception as e:
        # User account creation is critical - fail the onboarding if it fails
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user account during shop onboarding: {str(e)}. Shop onboarding requires user account creation."
        )
    
    db.commit()
    db.refresh(db_shop)
    db.refresh(db_owner)
    
    return db_shop, db_owner

def get_shop_by_id(db: Session, shop_id: int):
    """Get shop by ID"""
    return db.query(models.Shop).filter(models.Shop.id == shop_id).first()

def get_shop_by_code(db: Session, shop_code: str):
    """Get shop by shop_code"""
    return db.query(models.Shop).filter(models.Shop.shop_code == shop_code).first()

def get_owner_by_shop_id(db: Session, shop_id: int):
    """Get owner by shop_id"""
    return db.query(models.Owner).filter(models.Owner.shop_id == shop_id).first()

# Customer CRUD operations
def create_customer(db: Session, customer_data: schemas.CustomerCreate, shop_id: int):
    """Create a customer for a shop"""
    db_customer = models.Customer(
        shop_id=shop_id,
        customer_name=customer_data.customer_name,
        phone=customer_data.phone,
        email=customer_data.email,
        address=customer_data.address,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat()
    )
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

def get_customers_by_shop(db: Session, shop_id: int, skip: int = 0, limit: int = 100):
    """Get all customers for a shop"""
    return db.query(models.Customer).filter(
        models.Customer.shop_id == shop_id,
        models.Customer.is_active == True
    ).offset(skip).limit(limit).all()

def get_customer_by_id(db: Session, customer_id: int, shop_id: int):
    """Get customer by ID (must belong to shop)"""
    return db.query(models.Customer).filter(
        models.Customer.id == customer_id,
        models.Customer.shop_id == shop_id
    ).first()

# Root Admin operations
def get_all_shops(db: Session, skip: int = 0, limit: int = 100):
    """Get all shops (root admin only)"""
    return db.query(models.Shop).offset(skip).limit(limit).all()

def get_all_users(db: Session, skip: int = 0, limit: int = 100):
    """Get all users (root admin only)"""
    return db.query(models.User).offset(skip).limit(limit).all()

# Tenant Admin operations
def get_shop_staff(db: Session, shop_id: int, skip: int = 0, limit: int = 100):
    """Get all staff users for a shop (tenant admin only)"""
    return db.query(models.User).filter(
        models.User.shop_id == shop_id,
        models.User.role.in_(["tenant_admin", "staff"])
    ).offset(skip).limit(limit).all()

# State CRUD operations
def create_state(db: Session, state_data: schemas.StateCreate):
    """Create a new state"""
    db_state = models.State(**state_data.dict())
    db.add(db_state)
    db.commit()
    db.refresh(db_state)
    return db_state

def get_state_by_id(db: Session, state_id: int):
    """Get state by ID"""
    return db.query(models.State).filter(models.State.id == state_id).first()

def get_state_by_code(db: Session, state_code: str):
    """Get state by code (e.g., 'MH')"""
    return db.query(models.State).filter(models.State.code == state_code).first()

def get_state_by_name(db: Session, state_name: str):
    """Get state by name (e.g., 'Maharashtra')"""
    return db.query(models.State).filter(models.State.name == state_name).first()

def get_all_states(db: Session, skip: int = 0, limit: int = 100, active_only: bool = True):
    """Get all states"""
    query = db.query(models.State)
    if active_only:
        query = query.filter(models.State.is_active == True)
    return query.offset(skip).limit(limit).all()

def update_state(db: Session, state_id: int, state_data: schemas.StateCreate):
    """Update a state"""
    db_state = db.query(models.State).filter(models.State.id == state_id).first()
    if not db_state:
        return None
    for key, value in state_data.dict().items():
        setattr(db_state, key, value)
    db_state.updated_at = datetime.utcnow().isoformat()
    db.commit()
    db.refresh(db_state)
    return db_state

def create_shop_staff(db: Session, user_data: schemas.UserCreate, shop_id: int):
    """Create a staff user for a shop (tenant admin only)"""
    # Staff must be linked to shop
    db_user = create_user(db, user_data)
    db_user.shop_id = shop_id
    db_user.role = "staff"  # Force staff role for tenant-created users
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
