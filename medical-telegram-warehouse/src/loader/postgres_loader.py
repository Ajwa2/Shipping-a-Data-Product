"""
PostgreSQL Loader for raw messages
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


class PostgresLoader:
    """Loader for inserting data into PostgreSQL"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL must be set in .env or passed as parameter")
        
        self.engine = create_engine(self.database_url)
        self.Session = sessionmaker(bind=self.engine)
    
    def create_raw_schema(self):
        """Create raw schema if it doesn't exist"""
        with self.engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))
            conn.commit()
            print("Raw schema created/verified")
    
    def create_raw_table(self):
        """Create raw.telegram_messages table if it doesn't exist"""
        self.create_raw_schema()
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS raw.telegram_messages (
                    message_id BIGINT PRIMARY KEY,
                    channel_name VARCHAR(255) NOT NULL,
                    channel_title VARCHAR(255),
                    message_date TIMESTAMP,
                    message_text TEXT,
                    has_media BOOLEAN DEFAULT FALSE,
                    image_path VARCHAR(500),
                    views INTEGER DEFAULT 0,
                    forwards INTEGER DEFAULT 0,
                    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            print("Raw.telegram_messages table created/verified")
    
    def create_enriched_table(self):
        """Create enriched_messages table for YOLO detections"""
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS enriched_messages (
                    message_id BIGINT PRIMARY KEY,
                    channel_name VARCHAR(255),
                    message_date TIMESTAMP,
                    image_path VARCHAR(500),
                    detected_objects JSONB,
                    yolo_detections JSONB,
                    enriched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (message_id) REFERENCES raw_messages(message_id)
                )
            """))
            conn.commit()
            print("Enriched messages table created/verified")
    
    def load_from_json(self, json_path: Path, table_name: str = "raw.telegram_messages"):
        """
        Load messages from JSON file to PostgreSQL
        
        Args:
            json_path: Path to JSON file
            table_name: Target table name
        """
        if not json_path.exists():
            print(f"JSON file not found: {json_path}")
            return
        
        with open(json_path, 'r', encoding='utf-8') as f:
            messages = json.load(f)
        
        if not messages:
            print(f"No messages to load from {json_path}")
            return
        
        df = pd.DataFrame(messages)
        
        # Convert message_date to datetime
        if 'message_date' in df.columns:
            df['message_date'] = pd.to_datetime(df['message_date'], errors='coerce')
        
        # Ensure boolean columns are properly typed
        if 'has_media' in df.columns:
            df['has_media'] = df['has_media'].astype(bool)
        
        # Load to database (append mode, ignore duplicates)
        # Handle schema-qualified table names
        if '.' in table_name:
            schema, table = table_name.split('.', 1)
        else:
            schema, table = None, table_name
        
        try:
            df.to_sql(
                table,
                self.engine,
                schema=schema,
                if_exists='append',
                index=False,
                method='multi'
            )
            print(f"Loaded {len(df)} messages from {json_path.name} to {table_name}")
        except Exception as e:
            print(f"Error loading data: {e}")
            # Try inserting one by one to handle duplicates
            self._load_messages_one_by_one(messages, table_name)
    
    def _load_messages_one_by_one(self, messages: List[Dict], table_name: str):
        """Load messages one by one, skipping duplicates"""
        with self.Session() as session:
            for msg in messages:
                try:
                    # Check if message_id already exists
                    exists = session.execute(
                        text(f"SELECT 1 FROM {table_name} WHERE message_id = :msg_id"),
                        {"msg_id": msg["message_id"]}
                    ).fetchone()
                    
                    if not exists:
                        # Insert new message
                        df = pd.DataFrame([msg])
                        if 'message_date' in df.columns:
                            df['message_date'] = pd.to_datetime(df['message_date'], errors='coerce')
                        df.to_sql(
                            table_name,
                            self.engine,
                            if_exists='append',
                            index=False
                        )
                except Exception as e:
                    print(f"Error inserting message {msg.get('message_id')}: {e}")
                    continue
            
            session.commit()
    
    def load_from_directory(self, directory: Path, pattern: str = "*.json"):
        """
        Load all JSON files from a directory
        
        Args:
            directory: Directory containing JSON files
            pattern: File pattern to match
        """
        json_files = list(directory.glob(pattern))
        print(f"Found {len(json_files)} JSON files in {directory}")
        
        for json_file in json_files:
            if json_file.name.startswith("_"):  # Skip manifest files
                continue
            self.load_from_json(json_file)
    
    def get_table_count(self, table_name: str = "raw.telegram_messages") -> int:
        """Get row count from a table"""
        with self.engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            return result.scalar()
    
    def close(self):
        """Close database connection"""
        self.engine.dispose()


def load_messages_from_data_lake(
    base_path: str = "data",
    date_str: Optional[str] = None
):
    """
    Convenience function to load messages from data lake
    
    Args:
        base_path: Base directory for data
        date_str: Date string (YYYY-MM-DD), defaults to today
    """
    from datetime import datetime
    
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    loader = PostgresLoader()
    loader.create_raw_table()
    
    json_dir = Path(base_path) / "raw" / "telegram_messages" / date_str
    if json_dir.exists():
        loader.load_from_directory(json_dir)
    else:
        print(f"Directory not found: {json_dir}")
    
    count = loader.get_table_count("raw.telegram_messages")
    print(f"Total messages in database: {count}")
    loader.close()


if __name__ == "__main__":
    # Example usage
    load_messages_from_data_lake()
