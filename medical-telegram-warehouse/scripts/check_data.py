"""Quick script to check if data is in the database"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    # Check raw table
    result = conn.execute(text("SELECT COUNT(*) FROM raw.telegram_messages"))
    count = result.scalar()
    print(f"Messages in raw.telegram_messages: {count}")
    
    if count > 0:
        # Show sample
        sample = conn.execute(text("SELECT message_id, channel_name, message_date FROM raw.telegram_messages LIMIT 5"))
        print("\nSample messages:")
        for row in sample:
            print(f"  {row}")
