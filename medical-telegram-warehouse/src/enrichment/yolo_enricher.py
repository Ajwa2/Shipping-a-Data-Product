"""
YOLO Enricher for image object detection
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from ultralytics import YOLO
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()


class YOLOEnricher:
    """Enrich messages with YOLO object detection"""
    
    def __init__(self, model_path: str = "yolov8n.pt", database_url: Optional[str] = None):
        """
        Initialize YOLO enricher
        
        Args:
            model_path: Path to YOLO model file (will download if not exists)
            database_url: PostgreSQL connection URL
        """
        self.model = YOLO(model_path)
        self.database_url = database_url or os.getenv("DATABASE_URL")
        
        if self.database_url:
            self.engine = create_engine(self.database_url)
            self.Session = sessionmaker(bind=self.engine)
    
    def detect_objects(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Detect objects in an image using YOLO
        
        Args:
            image_path: Path to image file
            
        Returns:
            List of detection dictionaries
        """
        if not Path(image_path).exists():
            return []
        
        try:
            results = self.model(image_path)
            detections = []
            
            for result in results:
                for box in result.boxes:
                    detections.append({
                        "class": result.names[int(box.cls)],
                        "class_id": int(box.cls),
                        "confidence": float(box.conf.item()),
                        "bbox": box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                    })
            
            return detections
        except Exception as e:
            print(f"Error detecting objects in {image_path}: {e}")
            return []
    
    def enrich_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich a message dictionary with YOLO detections
        
        Args:
            message: Message dictionary with image_path
            
        Returns:
            Enriched message dictionary
        """
        image_path = message.get("image_path")
        
        if image_path and Path(image_path).exists():
            detections = self.detect_objects(image_path)
            message["yolo_detections"] = detections
            message["detected_objects"] = [d["class"] for d in detections]
            message["detection_count"] = len(detections)
        else:
            message["yolo_detections"] = []
            message["detected_objects"] = []
            message["detection_count"] = 0
        
        return message
    
    def enrich_from_database(self, limit: Optional[int] = None):
        """
        Enrich messages from database that have images but no enrichments
        
        Args:
            limit: Maximum number of messages to process
        """
        if not self.database_url:
            raise ValueError("Database URL required for database enrichment")
        
        with self.Session() as session:
            # Get messages with images that haven't been enriched
            query = text("""
                SELECT 
                    rm.message_id,
                    rm.channel_name,
                    rm.message_date,
                    rm.image_path
                FROM raw_messages rm
                LEFT JOIN enriched_messages em ON rm.message_id = em.message_id
                WHERE rm.has_media = TRUE 
                    AND rm.image_path IS NOT NULL
                    AND em.message_id IS NULL
                ORDER BY rm.message_date DESC
                LIMIT :limit
            """)
            
            result = session.execute(query, {"limit": limit or 1000})
            messages = result.fetchall()
            
            print(f"Found {len(messages)} messages to enrich")
            
            enriched_count = 0
            for msg in messages:
                message_dict = {
                    "message_id": msg[0],
                    "channel_name": msg[1],
                    "message_date": msg[2],
                    "image_path": msg[3]
                }
                
                enriched = self.enrich_message(message_dict)
                
                # Save to enriched_messages table
                try:
                    session.execute(
                        text("""
                            INSERT INTO enriched_messages 
                            (message_id, channel_name, message_date, image_path, detected_objects, yolo_detections)
                            VALUES (:message_id, :channel_name, :message_date, :image_path, 
                                    :detected_objects::jsonb, :yolo_detections::jsonb)
                            ON CONFLICT (message_id) DO UPDATE SET
                                detected_objects = EXCLUDED.detected_objects,
                                yolo_detections = EXCLUDED.yolo_detections,
                                enriched_at = CURRENT_TIMESTAMP
                        """),
                        {
                            "message_id": enriched["message_id"],
                            "channel_name": enriched["channel_name"],
                            "message_date": enriched["message_date"],
                            "image_path": enriched["image_path"],
                            "detected_objects": json.dumps(enriched["detected_objects"]),
                            "yolo_detections": json.dumps(enriched["yolo_detections"])
                        }
                    )
                    enriched_count += 1
                except Exception as e:
                    print(f"Error saving enrichment for message {enriched['message_id']}: {e}")
                    session.rollback()
                    continue
            
            session.commit()
            print(f"Enriched {enriched_count} messages")
    
    def get_detection_summary(self) -> Dict[str, Any]:
        """Get summary of detected objects"""
        if not self.database_url:
            return {}
        
        with self.Session() as session:
            query = text("""
                SELECT 
                    jsonb_array_elements_text(detected_objects) as object_class,
                    COUNT(*) as count
                FROM enriched_messages
                WHERE detected_objects IS NOT NULL
                GROUP BY object_class
                ORDER BY count DESC
            """)
            
            result = session.execute(query)
            summary = {row[0]: row[1] for row in result}
            return summary


if __name__ == "__main__":
    # Example usage
    enricher = YOLOEnricher()
    
    # Enrich from database
    enricher.enrich_from_database(limit=100)
    
    # Get summary
    summary = enricher.get_detection_summary()
    print("Detection summary:", summary)
