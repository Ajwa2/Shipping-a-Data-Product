"""
Dagster Pipeline Definition
Task 5 - Pipeline Orchestration

This is the main entry point for Dagster. Run with:
    dagster dev -f pipeline.py

Or use the script:
    python scripts/run_dagster.py
"""
from src.orchestration.pipeline import defs

# Export definitions for Dagster
__all__ = ["defs"]
