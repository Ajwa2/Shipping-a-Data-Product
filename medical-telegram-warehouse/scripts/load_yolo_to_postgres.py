"""
Load YOLO detection results from CSV to PostgreSQL
Task 3 - Data Enrichment
"""
import sys
import csv
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv()


def create_enriched_table(engine):
    """Create enriched_messages table if it doesn't exist"""
    with engine.connect() as conn:
        # Create raw schema if needed
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))
        
        # Create enriched_messages table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS raw.enriched_messages (
                message_id BIGINT PRIMARY KEY,
                channel_name VARCHAR(255) NOT NULL,
                image_path VARCHAR(500),
                detection_count INTEGER DEFAULT 0,
                image_category VARCHAR(50),
                confidence_score NUMERIC(5, 3),
                has_person BOOLEAN DEFAULT FALSE,
                has_product BOOLEAN DEFAULT FALSE,
                detected_objects TEXT,
                detections_json JSONB,
                enriched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()
        print("Raw.enriched_messages table created/verified")


def load_yolo_results(csv_path: Path, database_url: str):
    """
    Load YOLO detection results from CSV to PostgreSQL
    
    Args:
        csv_path: Path to YOLO detections CSV file
        database_url: PostgreSQL connection URL
    """
    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}")
        return
    
    print("=" * 60)
    print("Task 3: Load YOLO Detection Results to PostgreSQL")
    print("=" * 60)
    print(f"Loading from: {csv_path}")
    print()
    
    engine = create_engine(database_url)
    
    # Create table
    create_enriched_table(engine)
    
    # Read CSV and insert data
    rows_loaded = 0
    rows_skipped = 0
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        with engine.connect() as conn:
            for row in reader:
                try:
                    # Parse detected_objects (comma-separated string)
                    detected_objects = row.get('detected_objects', '')
                    
                    # Insert or update
                    # Cast JSON string to JSONB
                    detections_json_value = row.get('detections_json', '[]')
                    if not detections_json_value or detections_json_value == '':
                        detections_json_value = '[]'
                    
                    conn.execute(text("""
                        INSERT INTO raw.enriched_messages (
                            message_id,
                            channel_name,
                            image_path,
                            detection_count,
                            image_category,
                            confidence_score,
                            has_person,
                            has_product,
                            detected_objects,
                            detections_json
                        ) VALUES (
                            :message_id,
                            :channel_name,
                            :image_path,
                            :detection_count,
                            :image_category,
                            :confidence_score,
                            :has_person,
                            :has_product,
                            :detected_objects,
                            CAST(:detections_json AS JSONB)
                        )
                        ON CONFLICT (message_id) DO UPDATE SET
                            detection_count = EXCLUDED.detection_count,
                            image_category = EXCLUDED.image_category,
                            confidence_score = EXCLUDED.confidence_score,
                            has_person = EXCLUDED.has_person,
                            has_product = EXCLUDED.has_product,
                            detected_objects = EXCLUDED.detected_objects,
                            detections_json = EXCLUDED.detections_json,
                            enriched_at = CURRENT_TIMESTAMP
                    """), {
                        'message_id': int(row['message_id']),
                        'channel_name': row['channel_name'],
                        'image_path': row['image_path'],
                        'detection_count': int(row.get('detection_count', 0)),
                        'image_category': row.get('image_category', 'other'),
                        'confidence_score': float(row.get('confidence_score', 0.0)) if row.get('confidence_score') else None,
                        'has_person': row.get('has_person', 'False').lower() == 'true',
                        'has_product': row.get('has_product', 'False').lower() == 'true',
                        'detected_objects': detected_objects,
                        'detections_json': detections_json_value
                    })
                    rows_loaded += 1
                except Exception as e:
                    print(f"Error loading row for message_id {row.get('message_id')}: {e}")
                    rows_skipped += 1
                    continue
            
            conn.commit()
    
    print("\n" + "=" * 60)
    print(f"[SUCCESS] Load complete!")
    print(f"  Rows loaded: {rows_loaded}")
    if rows_skipped > 0:
        print(f"  Rows skipped: {rows_skipped}")
    print("=" * 60)
    print("\nNext step: Run dbt to create fct_image_detections")
    print("  cd medical_warehouse")
    print("  dbt run --select fct_image_detections")


if __name__ == "__main__":
    csv_path = project_root / "data" / "processed" / "yolo_detections.csv"
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("Error: DATABASE_URL not set in .env file")
        sys.exit(1)
    
    load_yolo_results(csv_path, database_url)
