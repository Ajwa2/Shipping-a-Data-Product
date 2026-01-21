"""
Standalone script to enrich messages with YOLO
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.enrichment.yolo_enricher import YOLOEnricher
from src.loader.postgres_loader import PostgresLoader

if __name__ == "__main__":
    # Create enriched table if needed
    loader = PostgresLoader()
    loader.create_enriched_table()
    loader.close()
    
    # Enrich messages
    enricher = YOLOEnricher()
    
    # Get limit from command line or use default
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    
    print(f"Enriching up to {limit} messages with YOLO...")
    enricher.enrich_from_database(limit=limit)
    
    # Get summary
    summary = enricher.get_detection_summary()
    print(f"\nDetection summary:")
    for obj_class, count in summary.items():
        print(f"  {obj_class}: {count}")
