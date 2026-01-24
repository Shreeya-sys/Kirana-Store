from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import models, schemas, crud, auth, database

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="KiranaFlow API", version="1.0")

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
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

@app.get("/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: schemas.UserResponse = Depends(auth.get_current_active_user)):
    return current_user

@app.post("/items/", response_model=schemas.ItemResponse)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(auth.get_current_active_user)):
    return crud.create_item(db=db, item=item)

@app.get("/items/", response_model=list[schemas.ItemResponse])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_items(db, skip=skip, limit=limit)

@app.post("/inventory/decant/{item_id}", response_model=schemas.ItemResponse)
def decant_inventory(item_id: int, db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(auth.get_current_active_user)):
    item = crud.decant_stock(db, item_id)
    if not item:
        raise HTTPException(status_code=400, detail="Decant failed: Item not found or insufficient bulk stock")
    return item

@app.post("/invoices/", response_model=schemas.InvoiceResponse)
def create_invoice(invoice: schemas.InvoiceCreate, db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(auth.get_current_active_user)):
    return crud.create_invoice(db=db, invoice=invoice)

@app.get("/ledger/{phone}", response_model=list[schemas.LedgerResponse])
def read_ledger(phone: str, db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(auth.get_current_active_user)):
    return crud.get_ledger(db, phone)
