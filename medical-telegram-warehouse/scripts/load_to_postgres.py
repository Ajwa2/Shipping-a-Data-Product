"""
Standalone script to load data from data lake to PostgreSQL
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.loader.postgres_loader import load_messages_from_data_lake

if __name__ == "__main__":
    # Load from today's data
    load_messages_from_data_lake()
    
    # Or specify a date: load_messages_from_data_lake(date_str="2024-01-15")
