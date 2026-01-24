from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import models, schemas, crud, auth, database
from sqlalchemy import text, event

# Create all tables - using database.Base which is the same Base used by all models
database.Base.metadata.create_all(bind=database.engine, checkfirst=True)

# Auto-migrate: Update shops and owners tables to match current schema
def migrate_tables_if_needed():
    """Automatically migrate shops and owners tables to match current schema"""
    try:
        with database.engine.begin() as conn:  # Use begin() for transaction
            # Disable foreign key checks temporarily
            conn.execute(text("PRAGMA foreign_keys=OFF"))
            
            # Migrate shops table
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='shops'
            """))
            if result.fetchone():
                # Check current schema
                result = conn.execute(text("PRAGMA table_info(shops)"))
                columns = result.fetchall()
                column_names = [col[1] for col in columns]
                
                # Check if hashed_password exists
                if 'hashed_password' not in column_names:
                    print("Auto-migrating: Updating shops table schema...")
                    
                    # Get existing data
                    result = conn.execute(text("SELECT * FROM shops"))
                    rows = result.fetchall()
                    old_column_names = [col[1] for col in columns]
                    
                    # Recreate table with correct schema
                    conn.execute(text("DROP TABLE IF EXISTS shops_old"))
                    conn.execute(text("ALTER TABLE shops RENAME TO shops_old"))
                    
                    conn.execute(text("""
                        CREATE TABLE shops (
                            id INTEGER NOT NULL PRIMARY KEY,
                            shop_name VARCHAR NOT NULL,
                            shop_code VARCHAR NOT NULL UNIQUE,
                            api_key VARCHAR NOT NULL UNIQUE,
                            hashed_password TEXT NOT NULL,
                            address TEXT,
                            city VARCHAR,
                            state VARCHAR,
                            pincode VARCHAR,
                            gst_number VARCHAR,
                            phone VARCHAR,
                            email VARCHAR,
                            email_password TEXT,
                            is_active BOOLEAN DEFAULT 1,
                            created_at VARCHAR,
                            updated_at VARCHAR
                        )
                    """))
                    
                    # Copy data (handle missing columns)
                    if rows:
                        # Set default password for existing shops (they'll need to reset)
                        default_password = "changeme123"  # Users should change this
                        default_hash = auth.get_password_hash(default_password)
                        
                        for row in rows:
                            row_dict = dict(zip(old_column_names, row))
                            
                            # Build INSERT with only existing columns
                            conn.execute(text("""
                                INSERT INTO shops (
                                    id, shop_name, shop_code, api_key, hashed_password,
                                    address, city, state, pincode, gst_number,
                                    phone, email, email_password, is_active, created_at, updated_at
                                ) VALUES (:id, :shop_name, :shop_code, :api_key, :hashed_password,
                                    :address, :city, :state, :pincode, :gst_number,
                                    :phone, :email, :email_password, :is_active, :created_at, :updated_at)
                            """), {
                                'id': row_dict.get('id'),
                                'shop_name': row_dict.get('shop_name', ''),
                                'shop_code': row_dict.get('shop_code', ''),
                                'api_key': row_dict.get('api_key', ''),
                                'hashed_password': default_hash,
                                'address': row_dict.get('address'),
                                'city': row_dict.get('city'),
                                'state': row_dict.get('state'),
                                'pincode': row_dict.get('pincode'),
                                'gst_number': row_dict.get('gst_number'),
                                'phone': row_dict.get('phone'),
                                'email': row_dict.get('email'),
                                'email_password': row_dict.get('email_password'),
                                'is_active': row_dict.get('is_active', 1),
                                'created_at': row_dict.get('created_at', ''),
                                'updated_at': row_dict.get('updated_at', '')
                            })
                    
                    conn.execute(text("DROP TABLE IF EXISTS shops_old"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_shops_shop_name ON shops (shop_name)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_shops_shop_code ON shops (shop_code)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_shops_api_key ON shops (api_key)"))
                    
                    print("Shops table migration completed!")
            
            # Migrate owners table
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='owners'
            """))
            if result.fetchone():
                # Check current schema
                result = conn.execute(text("PRAGMA table_info(owners)"))
                columns = result.fetchall()
                phone_col = [col for col in columns if col[1] == 'phone']
                
                # If phone exists and is NOT NULL
                if phone_col and phone_col[0][3] == 1:  # NOT NULL
                    print("Auto-migrating: Making owner.phone nullable...")
                    
                    # Get existing data
                    result = conn.execute(text("SELECT * FROM owners"))
                    rows = result.fetchall()
                    old_columns = [col[1] for col in columns]
                    
                    # Recreate table
                    conn.execute(text("DROP TABLE IF EXISTS owners_old"))
                    conn.execute(text("ALTER TABLE owners RENAME TO owners_old"))
                    
                    conn.execute(text("""
                        CREATE TABLE owners_new (
                            id INTEGER NOT NULL PRIMARY KEY,
                            shop_id INTEGER NOT NULL UNIQUE,
                            owner_name VARCHAR NOT NULL,
                            phone VARCHAR,
                            email VARCHAR,
                            aadhaar_number VARCHAR,
                            pan_number VARCHAR,
                            address TEXT,
                            created_at VARCHAR,
                            updated_at VARCHAR,
                            FOREIGN KEY(shop_id) REFERENCES shops (id)
                        )
                    """))
                    
                    # Copy data
                    if rows:
                        for row in rows:
                            row_dict = dict(zip(old_columns, row))
                            conn.execute(text("""
                                INSERT INTO owners_new (
                                    id, shop_id, owner_name, phone, email,
                                    aadhaar_number, pan_number, address, created_at, updated_at
                                ) VALUES (:id, :shop_id, :owner_name, :phone, :email,
                                    :aadhaar_number, :pan_number, :address, :created_at, :updated_at)
                            """), {
                                'id': row_dict.get('id'),
                                'shop_id': row_dict.get('shop_id'),
                                'owner_name': row_dict.get('owner_name', ''),
                                'phone': row_dict.get('phone'),
                                'email': row_dict.get('email'),
                                'aadhaar_number': row_dict.get('aadhaar_number'),
                                'pan_number': row_dict.get('pan_number'),
                                'address': row_dict.get('address'),
                                'created_at': row_dict.get('created_at', ''),
                                'updated_at': row_dict.get('updated_at', '')
                            })
                    
                    conn.execute(text("DROP TABLE IF EXISTS owners_old"))
                    conn.execute(text("ALTER TABLE owners_new RENAME TO owners"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_owners_phone ON owners (phone)"))
                    
                    print("Owners table migration completed!")
            
            # Migrate items table to add shop_id
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='items'
            """))
            if result.fetchone():
                result = conn.execute(text("PRAGMA table_info(items)"))
                columns = result.fetchall()
                column_names = [col[1] for col in columns]
                
                if 'shop_id' not in column_names:
                    print("Auto-migrating: Adding shop_id to items table...")
                    conn.execute(text("ALTER TABLE items ADD COLUMN shop_id INTEGER"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_items_shop_id ON items (shop_id)"))
                    print("Items table migration completed!")
            
            # Migrate invoices table to add shop_id
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='invoices'
            """))
            if result.fetchone():
                result = conn.execute(text("PRAGMA table_info(invoices)"))
                columns = result.fetchall()
                column_names = [col[1] for col in columns]
                
                if 'shop_id' not in column_names:
                    print("Auto-migrating: Adding shop_id to invoices table...")
                    conn.execute(text("ALTER TABLE invoices ADD COLUMN shop_id INTEGER"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_invoices_shop_id ON invoices (shop_id)"))
                    print("Invoices table migration completed!")
            
            # Migrate invoice_items table to add shop_id
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='invoice_items'
            """))
            if result.fetchone():
                result = conn.execute(text("PRAGMA table_info(invoice_items)"))
                columns = result.fetchall()
                column_names = [col[1] for col in columns]
                
                if 'shop_id' not in column_names:
                    print("Auto-migrating: Adding shop_id to invoice_items table...")
                    conn.execute(text("ALTER TABLE invoice_items ADD COLUMN shop_id INTEGER"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_invoice_items_shop_id ON invoice_items (shop_id)"))
                    print("Invoice_items table migration completed!")
            
            # Migrate ledgers table to add shop_id
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='ledgers'
            """))
            if result.fetchone():
                result = conn.execute(text("PRAGMA table_info(ledgers)"))
                columns = result.fetchall()
                column_names = [col[1] for col in columns]
                
                if 'shop_id' not in column_names:
                    print("Auto-migrating: Adding shop_id to ledgers table...")
                    conn.execute(text("ALTER TABLE ledgers ADD COLUMN shop_id INTEGER"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ledgers_shop_id ON ledgers (shop_id)"))
                    print("Ledgers table migration completed!")
            
            # Migrate stock_adjustments table to add shop_id
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='stock_adjustments'
            """))
            if result.fetchone():
                result = conn.execute(text("PRAGMA table_info(stock_adjustments)"))
                columns = result.fetchall()
                column_names = [col[1] for col in columns]
                
                if 'shop_id' not in column_names:
                    print("Auto-migrating: Adding shop_id to stock_adjustments table...")
                    conn.execute(text("ALTER TABLE stock_adjustments ADD COLUMN shop_id INTEGER"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_stock_adjustments_shop_id ON stock_adjustments (shop_id)"))
                    print("Stock_adjustments table migration completed!")
            
            # Create states table if it doesn't exist
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='states'
            """))
            if not result.fetchone():
                print("Auto-migrating: Creating states table...")
                conn.execute(text("""
                    CREATE TABLE states (
                        id INTEGER NOT NULL PRIMARY KEY,
                        name VARCHAR NOT NULL UNIQUE,
                        code VARCHAR NOT NULL UNIQUE,
                        gst_code VARCHAR,
                        is_active BOOLEAN DEFAULT 1,
                        created_at VARCHAR,
                        updated_at VARCHAR
                    )
                """))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_states_name ON states (name)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_states_code ON states (code)"))
                
                # Insert common Indian states
                indian_states = [
                    ("Andhra Pradesh", "AP", "37"),
                    ("Arunachal Pradesh", "AR", "12"),
                    ("Assam", "AS", "18"),
                    ("Bihar", "BR", "10"),
                    ("Chhattisgarh", "CG", "22"),
                    ("Goa", "GA", "30"),
                    ("Gujarat", "GJ", "24"),
                    ("Haryana", "HR", "06"),
                    ("Himachal Pradesh", "HP", "02"),
                    ("Jharkhand", "JH", "20"),
                    ("Karnataka", "KA", "29"),
                    ("Kerala", "KL", "32"),
                    ("Madhya Pradesh", "MP", "23"),
                    ("Maharashtra", "MH", "27"),
                    ("Manipur", "MN", "14"),
                    ("Meghalaya", "ML", "17"),
                    ("Mizoram", "MZ", "15"),
                    ("Nagaland", "NL", "13"),
                    ("Odisha", "OD", "21"),
                    ("Punjab", "PB", "03"),
                    ("Rajasthan", "RJ", "08"),
                    ("Sikkim", "SK", "11"),
                    ("Tamil Nadu", "TN", "33"),
                    ("Telangana", "TG", "36"),
                    ("Tripura", "TR", "16"),
                    ("Uttar Pradesh", "UP", "09"),
                    ("Uttarakhand", "UK", "05"),
                    ("West Bengal", "WB", "19"),
                    ("Delhi", "DL", "07"),
                    ("Jammu and Kashmir", "JK", "01"),
                    ("Ladakh", "LA", "38"),
                    ("Puducherry", "PY", "34"),
                    ("Chandigarh", "CH", "04"),
                    ("Dadra and Nagar Haveli and Daman and Diu", "DH", "26"),
                    ("Lakshadweep", "LD", "31"),
                    ("Andaman and Nicobar Islands", "AN", "35")
                ]
                
                for state_name, state_code, gst_code in indian_states:
                    conn.execute(text("""
                        INSERT INTO states (name, code, gst_code, is_active, created_at, updated_at)
                        VALUES (:name, :code, :gst_code, 1, datetime('now'), datetime('now'))
                    """), {
                        'name': state_name,
                        'code': state_code,
                        'gst_code': gst_code
                    })
                
                print("States table created with Indian states!")
            
            # Migrate shops table to add state_id
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='shops'
            """))
            if result.fetchone():
                result = conn.execute(text("PRAGMA table_info(shops)"))
                columns = result.fetchall()
                column_names = [col[1] for col in columns]
                
                if 'state_id' not in column_names:
                    print("Auto-migrating: Adding state_id to shops table...")
                    conn.execute(text("ALTER TABLE shops ADD COLUMN state_id INTEGER"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_shops_state_id ON shops (state_id)"))
                    
                    # Try to match existing state strings to state_id
                    result = conn.execute(text("SELECT id, state FROM shops WHERE state IS NOT NULL AND state != ''"))
                    shops_with_state = result.fetchall()
                    
                    for shop_id, state_name in shops_with_state:
                        # Try to find matching state
                        state_result = conn.execute(text("SELECT id FROM states WHERE name = :name OR code = :name"), {
                            'name': state_name
                        })
                        state_row = state_result.fetchone()
                        if state_row:
                            conn.execute(text("UPDATE shops SET state_id = :state_id WHERE id = :shop_id"), {
                                'state_id': state_row[0],
                                'shop_id': shop_id
                            })
                    
                    print("Shops table migration completed with state_id!")
            
            # Re-enable foreign key checks
            conn.execute(text("PRAGMA foreign_keys=ON"))
                    
    except Exception as e:
        print(f"Migration check failed: {e}")
        import traceback
        traceback.print_exc()

# Run migration on startup
migrate_tables_if_needed()

# Auto-create default root admin user if no users exist
def create_default_admin_if_needed():
    """Create default root admin user if database is empty"""
    try:
        db = database.SessionLocal()
        try:
            # Check if any users exist
            user_count = db.query(models.User).count()
            if user_count == 0:
                print("=" * 70)
                print("No users found. Creating default root admin user...")
                print("=" * 70)
                
                # Create user directly (bypass HTTPException from crud.create_user)
                import auth
                username = "shreeya"
                password = "shreeya"
                role = "root_admin"
                
                # Check if user already exists
                existing_user = crud.get_user_by_username(db, username=username)
                if existing_user:
                    print(f"User '{username}' already exists. Skipping creation.")
                else:
                    # Hash password
                    hashed_password = auth.get_password_hash(password)
                    
                    # Create user directly
                    db_user = models.User(
                        username=username,
                        hashed_password=hashed_password,
                        role=role
                    )
                    db.add(db_user)
                    db.commit()
                    db.refresh(db_user)
                    
                    print(f"✅ Default admin user created successfully!")
                    print(f"   Username: {db_user.username}")
                    print(f"   Role: {db_user.role}")
                    print(f"   ID: {db_user.id}")
                    print(f"\n   You can now login with:")
                    print(f"   username={username}, password={password}")
                    print("=" * 70)
            else:
                print(f"Database has {user_count} user(s). Skipping default user creation.")
        finally:
            db.close()
    except Exception as e:
        print(f"❌ ERROR: Could not create default admin user: {e}")
        import traceback
        traceback.print_exc()

app = FastAPI(title="KiranaFlow API", version="1.0")

# Create default admin on startup
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    create_default_admin_if_needed()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:*",
        "http://127.0.0.1:*",
        "http://localhost",
        "http://127.0.0.1",
        "*"  # Allow all origins in development (restrict in production)
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Manual endpoint to create default admin (for troubleshooting)
@app.post("/admin/create-default-user")
def create_default_user_manual(db: Session = Depends(get_db)):
    """Manually create default admin user (for troubleshooting)"""
    try:
        # Check if user exists
        existing_user = crud.get_user_by_username(db, username="shreeya")
        if existing_user:
            return {
                "message": "User 'shreeya' already exists",
                "user": {
                    "id": existing_user.id,
                    "username": existing_user.username,
                    "role": existing_user.role
                }
            }
        
        # Create user
        import auth
        hashed_password = auth.get_password_hash("shreeya")
        db_user = models.User(
            username="shreeya",
            hashed_password=hashed_password,
            role="root_admin"
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return {
            "message": "Default admin user created successfully",
            "user": {
                "id": db_user.id,
                "username": db_user.username,
                "role": db_user.role
            },
            "login": {
                "username": "shreeya",
                "password": "shreeya"
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

@app.get("/")
def read_root():
    return {"message": "Welcome to KiranaFlow API"}

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db), 
                current_user: Optional[models.User] = Depends(auth.get_current_user_optional)):
    """
    Create a user account.
    - If no authentication: Only allows creating root_admin (for initial setup)
    - Root admin: Can create any user (root_admin, tenant_admin, staff, customer)
    - Tenant admin: Can only create staff users for their shop
    """
    # Check if user already exists
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Permission checks
    if current_user is None:
        # No authentication - only allow root_admin creation (for initial setup)
        if user.role != "root_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthenticated requests can only create root_admin. Please authenticate first."
            )
    elif current_user.role == "root_admin":
        # Root admin can create any user
        pass
    elif current_user.role == "tenant_admin":
        # Tenant admin can only create staff users for their shop
        if user.role not in ["staff", "customer"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant admin can only create staff or customer users"
            )
        if not current_user.shop_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant admin must be linked to a shop"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only root admin or tenant admin can create users"
        )
    
    created_user = crud.create_user(db=db, user=user)
    
    # Link to shop if created by tenant admin
    if current_user and current_user.role == "tenant_admin" and current_user.shop_id:
        created_user.shop_id = current_user.shop_id
        db.add(created_user)
        db.commit()
        db.refresh(created_user)
    
    return created_user

@app.get("/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(auth.get_current_active_user)):
    """Get current authenticated user information"""
    return current_user

@app.post("/items/", response_model=schemas.ItemResponse)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db), 
                current_user: models.User = Depends(auth.require_tenant_admin_or_staff)):
    """Create an item for the authenticated shop"""
    if not current_user.shop_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not linked to a shop"
        )
    return crud.create_item(db=db, item=item, shop_id=current_user.shop_id)

@app.get("/items/", response_model=list[schemas.ItemResponse])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
               current_user: models.User = Depends(auth.require_tenant_admin_or_staff)):
    """List items for the authenticated shop"""
    if not current_user.shop_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not linked to a shop"
        )
    return crud.get_items_by_shop(db, current_user.shop_id, skip=skip, limit=limit)

@app.post("/inventory/decant/{item_id}", response_model=schemas.ItemResponse)
def decant_inventory(item_id: int, db: Session = Depends(get_db), 
                     current_user: models.User = Depends(auth.require_tenant_admin_or_staff)):
    """Decant inventory for an item in the authenticated shop"""
    if not current_user.shop_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not linked to a shop"
        )
    item = crud.decant_stock(db, item_id, shop_id=current_user.shop_id)
    if not item:
        raise HTTPException(status_code=400, detail="Decant failed: Item not found or insufficient bulk stock")
    return item

@app.post("/invoices/", response_model=schemas.InvoiceResponse)
def create_invoice(invoice: schemas.InvoiceCreate, db: Session = Depends(get_db), 
                   current_user: models.User = Depends(auth.require_tenant_admin_or_staff)):
    """Create an invoice for the authenticated shop"""
    if not current_user.shop_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not linked to a shop"
        )
    return crud.create_invoice(db=db, invoice=invoice, shop_id=current_user.shop_id)

@app.get("/ledger/{phone}", response_model=list[schemas.LedgerResponse])
def read_ledger(phone: str, db: Session = Depends(get_db), 
                current_user: models.User = Depends(auth.require_tenant_admin_or_staff)):
    """Get ledger entries for a customer phone in the authenticated shop"""
    if not current_user.shop_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not linked to a shop"
        )
    return crud.get_ledger(db, phone, shop_id=current_user.shop_id)

# Shop Onboarding Endpoints
@app.post("/shops/onboard", response_model=schemas.ShopOnboardResponse)
def onboard_shop(onboard_request: schemas.ShopOnboardRequest, db: Session = Depends(get_db)):
    """
    Onboard a new shop with owner details.
    This endpoint:
    - Creates a shop record
    - Creates an owner record
    - Generates a unique shop_code and API key
    - **Automatically creates a User account** for seamless login integration
      - Username: shop_code
      - Password: same as shop password
      - Role: admin
      - Linked to the shop via shop_id
    
    After onboarding, you can immediately login using:
    - Shop authentication: POST /shops/login (shop_code + password)
    - User authentication: POST /token (username=shop_code, password=shop_password)
    - API key: X-API-Key header
    """
    try:
        shop, owner = crud.create_shop_with_owner(db, onboard_request.shop, onboard_request.owner)
        
        # Get state information if state_id exists
        state_name = None
        state_code = None
        if shop.state_id:
            state_obj = crud.get_state_by_id(db, shop.state_id)
            if state_obj:
                state_name = state_obj.name
                state_code = state_obj.code
        
        return schemas.ShopOnboardResponse(
            shop=schemas.ShopResponse(
                id=shop.id,
                shop_name=shop.shop_name,
                shop_code=shop.shop_code,
                api_key=shop.api_key,
                address=shop.address,
                city=shop.city,
                state_id=shop.state_id,
                state=shop.state,  # Deprecated
                state_name=state_name,
                state_code=state_code,
                pincode=shop.pincode,
                gst_number=shop.gst_number,
                phone=shop.phone,
                email=shop.email,
                is_active=shop.is_active,
                created_at=shop.created_at
            ),
            owner=schemas.OwnerResponse(
                id=owner.id,
                shop_id=owner.shop_id,
                owner_name=owner.owner_name,
                phone=owner.phone,
                email=owner.email,
                aadhaar_number=owner.aadhaar_number,
                pan_number=owner.pan_number,
                address=owner.address,
                created_at=owner.created_at
            ),
            message=f"Shop onboarded successfully. Please save your API key securely. You can also login as a user with username: {shop.shop_code} and your shop password."
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the full error for debugging
        import traceback
        error_detail = str(e)
        print(f"Error onboarding shop: {error_detail}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to onboard shop: {error_detail}"
        )

@app.get("/shops/me", response_model=schemas.ShopResponse)
def get_shop_info(current_shop: models.Shop = Depends(auth.verify_api_key), db: Session = Depends(get_db)):
    """Get current shop information using API key"""
    # Get state information if state_id exists
    state_name = None
    state_code = None
    if current_shop.state_id:
        state_obj = crud.get_state_by_id(db, current_shop.state_id)
        if state_obj:
            state_name = state_obj.name
            state_code = state_obj.code
    
    # Create response with state information
    return schemas.ShopResponse(
        id=current_shop.id,
        shop_name=current_shop.shop_name,
        shop_code=current_shop.shop_code,
        api_key=current_shop.api_key,
        address=current_shop.address,
        city=current_shop.city,
        state_id=current_shop.state_id,
        state=current_shop.state,  # Deprecated
        state_name=state_name,
        state_code=state_code,
        pincode=current_shop.pincode,
        gst_number=current_shop.gst_number,
        phone=current_shop.phone,
        email=current_shop.email,
        is_active=current_shop.is_active,
        created_at=current_shop.created_at
    )

@app.get("/shops/{shop_id}/owner", response_model=schemas.OwnerResponse)
def get_shop_owner(shop_id: int, db: Session = Depends(get_db), current_shop: models.Shop = Depends(auth.verify_api_key)):
    """Get owner information for the authenticated shop"""
    # Verify that the shop_id matches the authenticated shop
    if current_shop.id != shop_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own shop's owner information"
        )
    
    owner = crud.get_owner_by_shop_id(db, shop_id)
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Owner information not found"
        )
    return owner

# Shop Authentication Endpoint
class ShopLoginRequest(BaseModel):
    shop_code: str
    password: str

@app.post("/shops/login", response_model=schemas.ShopResponse)
def shop_login(login_data: ShopLoginRequest, db: Session = Depends(get_db)):
    """
    Login for shops using shop_code and password.
    Returns shop information including API key.
    """
    shop = auth.authenticate_shop(db, login_data.shop_code, login_data.password)
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid shop code or password"
        )
    
    # Get state information if state_id exists
    state_name = None
    state_code = None
    if shop.state_id:
        state_obj = crud.get_state_by_id(db, shop.state_id)
        if state_obj:
            state_name = state_obj.name
            state_code = state_obj.code
    
    # Create response with state information
    return schemas.ShopResponse(
        id=shop.id,
        shop_name=shop.shop_name,
        shop_code=shop.shop_code,
        api_key=shop.api_key,
        address=shop.address,
        city=shop.city,
        state_id=shop.state_id,
        state=shop.state,  # Deprecated
        state_name=state_name,
        state_code=state_code,
        pincode=shop.pincode,
        gst_number=shop.gst_number,
        phone=shop.phone,
        email=shop.email,
        is_active=shop.is_active,
        created_at=shop.created_at
    )

# Root Admin Endpoints (Internal API)
@app.get("/admin/shops", response_model=list[schemas.ShopResponse])
def list_all_shops(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), 
                   current_user: models.User = Depends(auth.require_root_admin)):
    """List all shops - Root admin only"""
    shops = crud.get_all_shops(db, skip=skip, limit=limit)
    return shops

@app.get("/admin/users", response_model=list[schemas.UserResponse])
def list_all_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                   current_user: models.User = Depends(auth.require_root_admin)):
    """List all users - Root admin only"""
    users = crud.get_all_users(db, skip=skip, limit=limit)
    return users

# Tenant Admin Endpoints
@app.get("/tenant/staff", response_model=list[schemas.UserResponse])
def list_shop_staff(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                    current_user: models.User = Depends(auth.require_tenant_admin)):
    """List all staff for the tenant admin's shop"""
    staff = crud.get_shop_staff(db, current_user.shop_id, skip=skip, limit=limit)
    return staff

@app.post("/tenant/staff", response_model=schemas.UserResponse)
def create_staff(user: schemas.UserCreate, db: Session = Depends(get_db),
                 current_user: models.User = Depends(auth.require_tenant_admin)):
    """Create a staff user for the tenant admin's shop"""
    # Force staff role
    user.role = "staff"
    return crud.create_shop_staff(db, user, current_user.shop_id)

# Customer Management Endpoints
@app.post("/customers/", response_model=schemas.CustomerResponse)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db),
                    current_user: models.User = Depends(auth.require_tenant_admin_or_staff)):
    """Create a customer for the authenticated shop"""
    return crud.create_customer(db, customer, current_user.shop_id)

@app.get("/customers/", response_model=list[schemas.CustomerResponse])
def list_customers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                   current_user: models.User = Depends(auth.require_tenant_admin_or_staff)):
    """List all customers for the authenticated shop"""
    return crud.get_customers_by_shop(db, current_user.shop_id, skip=skip, limit=limit)

@app.get("/customers/{customer_id}", response_model=schemas.CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db),
                 current_user: models.User = Depends(auth.require_tenant_admin_or_staff)):
    """Get customer by ID (must belong to authenticated shop)"""
    customer = crud.get_customer_by_id(db, customer_id, current_user.shop_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    return customer

# State Management Endpoints
@app.post("/states/", response_model=schemas.StateResponse)
def create_state(state: schemas.StateCreate, db: Session = Depends(get_db),
                 current_user: models.User = Depends(auth.require_root_admin)):
    """Create a new state - Root admin only"""
    # Check if state with same code or name already exists
    existing = crud.get_state_by_code(db, state.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"State with code '{state.code}' already exists"
        )
    existing = crud.get_state_by_name(db, state.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"State with name '{state.name}' already exists"
        )
    return crud.create_state(db, state)

@app.get("/states/", response_model=list[schemas.StateResponse])
def list_states(skip: int = 0, limit: int = 100, active_only: bool = True, 
                db: Session = Depends(get_db)):
    """List all states (public endpoint, no authentication required)"""
    return crud.get_all_states(db, skip=skip, limit=limit, active_only=active_only)

@app.get("/states/{state_id}", response_model=schemas.StateResponse)
def get_state(state_id: int, db: Session = Depends(get_db)):
    """Get state by ID (public endpoint)"""
    state = crud.get_state_by_id(db, state_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="State not found"
        )
    return state

@app.get("/states/code/{state_code}", response_model=schemas.StateResponse)
def get_state_by_code(state_code: str, db: Session = Depends(get_db)):
    """Get state by code (e.g., 'MH') - public endpoint"""
    state = crud.get_state_by_code(db, state_code)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"State with code '{state_code}' not found"
        )
    return state

@app.put("/states/{state_id}", response_model=schemas.StateResponse)
def update_state(state_id: int, state: schemas.StateCreate, db: Session = Depends(get_db),
                 current_user: models.User = Depends(auth.require_root_admin)):
    """Update a state - Root admin only"""
    updated_state = crud.update_state(db, state_id, state)
    if not updated_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="State not found"
        )
    return updated_state
