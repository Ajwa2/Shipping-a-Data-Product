"""
Script to run Dagster development server
Task 5 - Pipeline Orchestration
"""
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    
    print("=" * 70)
    print("Dagster Pipeline Orchestration")
    print("=" * 70)
    print()
    print("Starting Dagster development server...")
    print()
    print("Access the Dagster UI at:")
    print("  http://localhost:3000")
    print()
    print("Pipeline Operations:")
    print("  1. scrape_telegram_data - Scrape Telegram channels")
    print("  2. load_raw_to_postgres - Load data to PostgreSQL")
    print("  3. run_dbt_transformations - Run dbt models")
    print("  4. run_yolo_enrichment - Run YOLO object detection")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 70)
    print()
    
    # Change to project root
    import os
    os.chdir(project_root)
    
    # Run dagster dev
    try:
        subprocess.run(
            ["dagster", "dev", "-f", "pipeline.py"],
            cwd=project_root
        )
    except KeyboardInterrupt:
        print("\n\nShutting down Dagster server...")
        sys.exit(0)
    except FileNotFoundError:
        print("ERROR: Dagster not found. Install with:")
        print("  pip install dagster dagster-webserver")
        sys.exit(1)
