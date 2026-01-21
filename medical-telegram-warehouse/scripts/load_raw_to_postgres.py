"""
Task 2 - Load Raw Data to PostgreSQL
Loads JSON files from data lake into raw.telegram_messages table
"""
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.loader.postgres_loader import PostgresLoader


def load_all_from_data_lake(base_path: str = "data", date_str: str = None):
    """
    Load all JSON files from data lake to PostgreSQL raw schema
    
    Args:
        base_path: Base directory for data
        date_str: Date string (YYYY-MM-DD), defaults to today
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    print("=" * 60)
    print("Task 2: Load Raw Data to PostgreSQL")
    print("=" * 60)
    print(f"Loading data from: {base_path}/raw/telegram_messages/{date_str}/")
    print()
    
    loader = PostgresLoader()
    
    try:
        # Create raw schema and table
        loader.create_raw_table()
        
        # Load from today's directory
        json_dir = Path(base_path) / "raw" / "telegram_messages" / date_str
        if json_dir.exists():
            loader.load_from_directory(json_dir)
        else:
            print(f"Warning: Directory not found: {json_dir}")
            print("Trying to load from all available dates...")
            
            # Try loading from all available dates
            base_json_dir = Path(base_path) / "raw" / "telegram_messages"
            if base_json_dir.exists():
                date_dirs = [d for d in base_json_dir.iterdir() if d.is_dir()]
                for date_dir in date_dirs:
                    print(f"\nLoading from {date_dir.name}...")
                    loader.load_from_directory(date_dir)
        
        # Get final count
        count = loader.get_table_count("raw.telegram_messages")
        print("\n" + "=" * 60)
        print(f"[SUCCESS] Load complete!")
        print(f"  Total messages in raw.telegram_messages: {count}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError loading data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        loader.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Load raw Telegram data from data lake to PostgreSQL"
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Date string (YYYY-MM-DD) to load. Defaults to today."
    )
    parser.add_argument(
        "--base-path",
        type=str,
        default="data",
        help="Base directory for data storage"
    )
    
    args = parser.parse_args()
    
    load_all_from_data_lake(base_path=args.base_path, date_str=args.date)
