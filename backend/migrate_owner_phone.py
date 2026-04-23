"""
Migration script to make owner.phone nullable in the database.
Run this once to update the existing database schema.
"""
from sqlalchemy import create_engine, text
from database import SQLALCHEMY_DATABASE_URL

def migrate_owner_phone():
    """Make owner.phone nullable in SQLite database"""
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    
    with engine.connect() as conn:
        # SQLite doesn't support ALTER COLUMN directly, so we need to:
        # 1. Create new table with correct schema
        # 2. Copy data
        # 3. Drop old table
        # 4. Rename new table
        
        # Check if owners table exists
        result = conn.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='owners'
        """))
        if not result.fetchone():
            print("Owners table doesn't exist yet. No migration needed.")
            return
        
        # Check current schema
        result = conn.execute(text("PRAGMA table_info(owners)"))
        columns = result.fetchall()
        phone_col = [col for col in columns if col[1] == 'phone']
        
        if phone_col and phone_col[0][3] == 0:  # NOT NULL (3rd element is notnull flag)
            print("Migrating owners table: making phone nullable...")
            
            # SQLite migration: recreate table
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
            conn.execute(text("""
                INSERT INTO owners_new 
                SELECT * FROM owners
            """))
            
            # Drop old table
            conn.execute(text("DROP TABLE owners"))
            
            # Rename new table
            conn.execute(text("ALTER TABLE owners_new RENAME TO owners"))
            
            # Recreate index
            conn.execute(text("CREATE INDEX ix_owners_phone ON owners (phone)"))
            
            conn.commit()
            print("Migration completed successfully!")
        else:
            print("Phone column is already nullable. No migration needed.")

if __name__ == "__main__":
    try:
        migrate_owner_phone()
    except Exception as e:
        print(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
