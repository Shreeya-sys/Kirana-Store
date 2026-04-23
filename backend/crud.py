from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import models, schemas, auth

def _schema_to_dict(obj):
    """Pydantic v1 uses .dict(), v2 uses .model_dump()"""
    return getattr(obj, "model_dump", getattr(obj, "dict"))()

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
    db_item = models.Item(**_schema_to_dict(item))
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

def get_item_by_id(db: Session, item_id: int, shop_id: int):
    """Get an item by ID (must belong to shop)"""
    return db.query(models.Item).filter(
        models.Item.id == item_id,
        models.Item.shop_id == shop_id
    ).first()

def update_item(db: Session, item_id: int, item_data: schemas.ItemCreate, shop_id: int):
    """Update an item for a shop"""
    db_item = get_item_by_id(db, item_id, shop_id)
    if not db_item:
        return None
    for key, value in _schema_to_dict(item_data).items():
        setattr(db_item, key, value)
    db.commit()
    db.refresh(db_item)
    return db_item

def delete_item(db: Session, item_id: int, shop_id: int):
    """Delete an item for a shop"""
    db_item = get_item_by_id(db, item_id, shop_id)
    if not db_item:
        return None
    db.delete(db_item)
    db.commit()
    return db_item

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
    
    # Validate shop_name is not empty
    if not shop_data.shop_name or not shop_data.shop_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shop name is required and cannot be empty"
        )
    
    # Validate owner_name is not empty
    if not owner_data.owner_name or not owner_data.owner_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner name is required and cannot be empty"
        )
    
    # Validate password length (or apply default for admin-created stores)
    password_value = shop_data.password or "changeme123"
    if len(password_value) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )
    
    # Hash the password
    try:
        hashed_password = auth.get_password_hash(password_value)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password hashing failed: {str(e)}"
        )
    
    # Trim and validate shop name
    shop_name_trimmed = shop_data.shop_name.strip()
    if not shop_name_trimmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shop name cannot be empty or only whitespace"
        )
    
    # Check for duplicate shop names (case-insensitive, only active shops)
    shop_name_lower = shop_name_trimmed.lower()
    
    # Ensure we have a valid shop name to compare
    if not shop_name_lower or len(shop_name_lower) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shop name cannot be empty after trimming"
        )
    
    # Query active shops and compare in Python (more reliable)
    # Filter: is_active must be explicitly True (not None, not False)
    # Get all shops first, then filter in Python to avoid SQLAlchemy issues
    all_shops = db.query(models.Shop).all()
    all_active_shops = [
        shop for shop in all_shops 
        if shop.is_active == True 
        and shop.shop_name 
        and shop.shop_name.strip()
    ]
    
    # Compare in Python - check if any active shop has the same name (case-insensitive)
    existing_shops_with_same_name = []
    print(f"[SHOP] Checking duplicate for shop name: '{shop_name_trimmed}' (lowercase: '{shop_name_lower}')")
    print(f"   Found {len(all_active_shops)} active shops in database")
    
    # Debug: List all existing shop names
    if all_active_shops:
        print(f"   Existing shop names in DB:")
        for idx, shop in enumerate(all_active_shops, 1):
            shop_name_display = shop.shop_name.strip() if shop.shop_name else "(None)"
            print(f"      {idx}. '{shop_name_display}' (ID: {shop.id}, Code: {shop.shop_code}, Active: {shop.is_active})")
    
    # Only check shops that have a non-empty shop_name
    # Since we already filtered in Python, all shops should have valid names
    for shop in all_active_shops:
        # Double-check that shop_name exists and is not empty
        if not shop.shop_name or not shop.shop_name.strip():
            print(f"   [WARN] Skipping shop ID {shop.id} - has empty shop_name")
            continue
            
        existing_name_trimmed = shop.shop_name.strip()
        existing_name_lower = existing_name_trimmed.lower()
        
        # Ensure both names are non-empty before comparing
        if not existing_name_lower or not shop_name_lower:
            print("   [WARN] Skipping comparison - one name is empty")
            continue
        
        # Debug comparison - show exact values
        print(f"   Comparing: '{shop_name_trimmed}' (lower: '{shop_name_lower}') vs '{existing_name_trimmed}' (lower: '{existing_name_lower}')")
        print(f"      Lengths: new={len(shop_name_lower)}, existing={len(existing_name_lower)}")
        print(f"      Are they equal? {existing_name_lower == shop_name_lower}")
        
        # Strict equality check - must be exactly the same (case-insensitive)
        # Use == for exact string comparison
        if existing_name_lower == shop_name_lower:
            print(f"   [WARN] MATCH FOUND: '{existing_name_trimmed}' matches '{shop_name_trimmed}'")
            existing_shops_with_same_name.append(shop)
        else:
            print("   [OK] No match - names are different")
    
    if existing_shops_with_same_name:
        print(f"[SHOP] Duplicate found: {len(existing_shops_with_same_name)} shop(s) with name '{shop_name_trimmed}'")
        existing_shop_codes = [s.shop_code for s in existing_shops_with_same_name]
        existing_shop_ids = [s.id for s in existing_shops_with_same_name]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A shop with the name '{shop_name_trimmed}' already exists (Shop IDs: {', '.join(map(str, existing_shop_ids))}, Shop Codes: {', '.join(existing_shop_codes)}). Please use a different shop name, or if you're testing, you can delete the existing shop using DELETE /admin/shops/{existing_shops_with_same_name[0].id} (root admin only)."
        )
    else:
        print(f"[SHOP] No duplicates found for '{shop_name_trimmed}' - proceeding with creation")
    
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
    
    # Create shop (use trimmed name)
    db_shop = models.Shop(
        shop_name=shop_name_trimmed,
        shop_code=shop_code,
        api_key=api_key,
        hashed_password=hashed_password,
        address=shop_data.address,
        city=shop_data.city,
        parent_shop_id=shop_data.parent_shop_id,
        store_type=shop_data.store_type or "main",
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
                password=password_value,  # Same password as shop for unified auth
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

def get_child_shops(db: Session, parent_shop_id: int, skip: int = 0, limit: int = 100):
    """Get child shops for a parent shop"""
    return db.query(models.Shop).filter(
        models.Shop.parent_shop_id == parent_shop_id
    ).offset(skip).limit(limit).all()

def update_shop_admin(db: Session, shop_id: int, shop_data: schemas.ShopAdminUpdate):
    """Update shop details as root admin"""
    db_shop = get_shop_by_id(db, shop_id)
    if not db_shop:
        return None

    payload = _schema_to_dict(shop_data)
    for key, value in payload.items():
        if value is None:
            continue
        if key == "password":
            db_shop.hashed_password = auth.get_password_hash(value)
        elif key == "shop_name":
            db_shop.shop_name = value.strip() if isinstance(value, str) else value
        else:
            setattr(db_shop, key, value)

    db_shop.updated_at = datetime.utcnow().isoformat()
    db.commit()
    db.refresh(db_shop)
    return db_shop

def soft_delete_shop(db: Session, shop_id: int):
    """Soft delete shop and deactivate linked users"""
    db_shop = get_shop_by_id(db, shop_id)
    if not db_shop:
        return None
    db_shop.is_active = False
    db_shop.updated_at = datetime.utcnow().isoformat()
    users = db.query(models.User).filter(models.User.shop_id == shop_id).all()
    for user in users:
        user.is_active = False
    db.commit()
    db.refresh(db_shop)
    return db_shop

def hard_delete_shop(db: Session, shop_id: int):
    """Hard delete a shop and related records."""
    db_shop = get_shop_by_id(db, shop_id)
    if not db_shop:
        return None

    # Prevent deleting a parent that still has branches.
    child_count = db.query(models.Shop).filter(models.Shop.parent_shop_id == shop_id).count()
    if child_count > 0:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete this store because it has {child_count} sub-store(s). Delete sub-stores first."
        )

    db.query(models.StockAdjustment).filter(models.StockAdjustment.shop_id == shop_id).delete()
    db.query(models.InvoiceItem).filter(models.InvoiceItem.shop_id == shop_id).delete()
    db.query(models.Invoice).filter(models.Invoice.shop_id == shop_id).delete()
    db.query(models.Ledger).filter(models.Ledger.shop_id == shop_id).delete()
    db.query(models.Item).filter(models.Item.shop_id == shop_id).delete()
    db.query(models.Customer).filter(models.Customer.shop_id == shop_id).delete()
    db.query(models.User).filter(models.User.shop_id == shop_id).delete()
    db.query(models.Owner).filter(models.Owner.shop_id == shop_id).delete()
    db.delete(db_shop)
    db.commit()
    return db_shop

def upsert_owner_for_shop(db: Session, shop_id: int, owner_data: schemas.OwnerBase):
    """Create or update owner for a shop"""
    db_owner = get_owner_by_shop_id(db, shop_id)
    if db_owner is None:
        db_owner = models.Owner(
            shop_id=shop_id,
            owner_name=owner_data.owner_name,
            phone=owner_data.phone,
            email=owner_data.email,
            aadhaar_number=owner_data.aadhaar_number,
            pan_number=owner_data.pan_number,
            address=owner_data.address,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        )
        db.add(db_owner)
    else:
        db_owner.owner_name = owner_data.owner_name
        db_owner.phone = owner_data.phone
        db_owner.email = owner_data.email
        db_owner.aadhaar_number = owner_data.aadhaar_number
        db_owner.pan_number = owner_data.pan_number
        db_owner.address = owner_data.address
        db_owner.updated_at = datetime.utcnow().isoformat()
    db.commit()
    db.refresh(db_owner)
    return db_owner

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

def update_customer(db: Session, customer_id: int, customer_data: schemas.CustomerCreate, shop_id: int):
    """Update customer details for a shop"""
    db_customer = get_customer_by_id(db, customer_id, shop_id)
    if not db_customer:
        return None
    for key, value in _schema_to_dict(customer_data).items():
        setattr(db_customer, key, value)
    db_customer.updated_at = datetime.utcnow().isoformat()
    db.commit()
    db.refresh(db_customer)
    return db_customer

def delete_customer(db: Session, customer_id: int, shop_id: int):
    """Soft delete customer for a shop"""
    db_customer = get_customer_by_id(db, customer_id, shop_id)
    if not db_customer:
        return None
    db_customer.is_active = False
    db_customer.updated_at = datetime.utcnow().isoformat()
    db.commit()
    db.refresh(db_customer)
    return db_customer

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
    db_state = models.State(**_schema_to_dict(state_data))
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
    for key, value in _schema_to_dict(state_data).items():
        setattr(db_state, key, value)
    db_state.updated_at = datetime.utcnow().isoformat()
    db.commit()
    db.refresh(db_state)
    return db_state

def delete_state(db: Session, state_id: int):
    """Soft delete a state by setting is_active to False"""
    db_state = db.query(models.State).filter(models.State.id == state_id).first()
    if not db_state:
        return None
    db_state.is_active = False
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
