"""
Script to run the Dagster pipeline manually
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dagster import Definitions
from src.orchestration.pipeline import defs

if __name__ == "__main__":
    # This can be used with: dagster dev
    # Or run individual assets with: dagster asset materialize -m src.orchestration.pipeline scrape_telegram_channels
    print("Dagster definitions loaded. Use 'dagster dev' to start the Dagster UI")
    print("Or run: dagster asset materialize -m src.orchestration.pipeline <asset_name>")
