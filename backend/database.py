from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Use a database location outside OneDrive to avoid sync conflicts
# Store in user's local AppData folder
db_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "KiranaFlow")
os.makedirs(db_dir, exist_ok=True)
db_path = os.path.join(db_dir, "kiranaflow.db")

SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
