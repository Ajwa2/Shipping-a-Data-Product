"""
Test script to verify Dagster pipeline loads correctly
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from pipeline import defs
    
    print("=" * 70)
    print("DAGSTER PIPELINE - VERIFICATION")
    print("=" * 70)
    print()
    print(f"✓ Pipeline loaded successfully!")
    print()
    print(f"Jobs: {len(defs.jobs)}")
    for job in defs.jobs:
        print(f"  - {job.name}")
        print(f"    Description: {job.description or 'N/A'}")
        print(f"    Ops: {len(job.nodes)}")
        for node in job.nodes:
            print(f"      • {node.name}")
    print()
    print(f"Schedules: {len(defs.schedules)}")
    for schedule in defs.schedules:
        print(f"  - {schedule.name}")
        print(f"    Cron: {schedule.cron_schedule}")
        print(f"    Status: {schedule.default_status}")
    print()
    print(f"Sensors: {len(defs.sensors)}")
    for sensor in defs.sensors:
        print(f"  - {sensor.name}")
    print()
    print("=" * 70)
    print("Pipeline is ready to run!")
    print()
    print("To start Dagster UI:")
    print("  python scripts/run_dagster.py")
    print("  or")
    print("  dagster dev -f pipeline.py")
    print()
    print("Then access: http://localhost:3000")
    print("=" * 70)
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
