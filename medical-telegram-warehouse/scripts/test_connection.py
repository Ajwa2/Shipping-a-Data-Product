"""
Quick script to test database connection
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/medical_warehouse")

print("Testing database connection...")
print(f"Connection string: {DATABASE_URL.split('@')[0]}@...")
print()

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print("[SUCCESS] Database connection successful!")
        print(f"PostgreSQL version: {version.split(',')[0]}")
        print()
        
        # Check if database exists and has tables
        try:
            result = conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'raw'"))
            raw_tables = result.fetchone()[0]
            print(f"Raw schema tables: {raw_tables}")
            
            result = conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"))
            public_tables = result.fetchone()[0]
            print(f"Public schema tables: {public_tables}")
            
            if raw_tables > 0:
                result = conn.execute(text("SELECT COUNT(*) FROM raw.telegram_messages"))
                count = result.fetchone()[0]
                print(f"Raw messages: {count}")
            
        except Exception as e:
            print(f"Note: {e}")
            print("Database exists but may not have data loaded yet.")
            print("Run: python scripts/load_raw_to_postgres.py")
        
except Exception as e:
    print("[ERROR] Connection failed!")
    print(f"Error: {e}")
    print()
    print("Possible solutions:")
    print("1. Install Docker Desktop and run: docker compose up -d")
    print("2. Install PostgreSQL locally")
    print("3. Use a cloud PostgreSQL service")
    print()
    print("See SETUP_DATABASE.md for detailed instructions.")
