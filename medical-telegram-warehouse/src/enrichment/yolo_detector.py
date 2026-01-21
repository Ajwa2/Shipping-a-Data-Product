"""
YOLO Object Detection for Telegram Images
Task 3 - Data Enrichment with Object Detection
"""
import csv
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from ultralytics import YOLO
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class YOLODetector:
    """
    YOLO-based object detector for Telegram images
    Uses YOLOv8 nano model for efficient detection
    """
    
    # COCO class IDs for relevant objects
    # Person: 0, Bottle: 39, Cup: 41, etc.
    PERSON_CLASS = 0
    PRODUCT_CLASSES = {
        39: 'bottle',
        40: 'wine glass',
        41: 'cup',
        44: 'bowl',
        46: 'banana',  # Sometimes detects fruits as products
        47: 'apple',
        48: 'sandwich',
        49: 'orange',
        67: 'cell phone',  # Sometimes products are shown with phones
    }
    
    def __init__(self, model_path: str = "yolov8n.pt", confidence_threshold: float = 0.25):
        """
        Initialize YOLO detector
        
        Args:
            model_path: Path to YOLO model (will download if not exists)
            confidence_threshold: Minimum confidence for detections
        """
        logger.info(f"Loading YOLO model: {model_path}")
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        logger.info("YOLO model loaded successfully")
    
    def detect_objects(self, image_path: Path) -> List[Dict]:
        """
        Detect objects in an image
        
        Args:
            image_path: Path to image file
            
        Returns:
            List of detection dictionaries with class, confidence, bbox
        """
        if not image_path.exists():
            logger.warning(f"Image not found: {image_path}")
            return []
        
        try:
            # Run inference
            results = self.model(str(image_path), conf=self.confidence_threshold, verbose=False)
            
            detections = []
            for result in results:
                if result.boxes is not None:
                    for box in result.boxes:
                        class_id = int(box.cls.item())
                        confidence = float(box.conf.item())
                        class_name = result.names[class_id]
                        
                        # Get bounding box coordinates
                        bbox = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                        
                        detections.append({
                            'class_id': class_id,
                            'class_name': class_name,
                            'confidence': confidence,
                            'bbox': bbox
                        })
            
            return detections
            
        except Exception as e:
            logger.error(f"Error detecting objects in {image_path}: {e}")
            return []
    
    def classify_image(self, detections: List[Dict]) -> Tuple[str, float]:
        """
        Classify image based on detected objects
        
        Classification scheme:
        - promotional: Contains person + product (someone showing/holding item)
        - product_display: Contains bottle/container, no person
        - lifestyle: Contains person, no product
        - other: Neither detected
        
        Args:
            detections: List of detection dictionaries
            
        Returns:
            Tuple of (category, confidence_score)
        """
        if not detections:
            return ('other', 0.0)
        
        # Extract detected classes
        class_ids = [d['class_id'] for d in detections]
        confidences = [d['confidence'] for d in detections]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Check for person
        has_person = self.PERSON_CLASS in class_ids
        
        # Check for products (bottles, containers, etc.)
        has_product = any(cid in self.PRODUCT_CLASSES for cid in class_ids)
        
        # Classify based on presence of person and product
        if has_person and has_product:
            return ('promotional', avg_confidence)
        elif has_product and not has_person:
            return ('product_display', avg_confidence)
        elif has_person and not has_product:
            return ('lifestyle', avg_confidence)
        else:
            return ('other', avg_confidence)
    
    def process_image(self, image_path: Path, message_id: int, channel_name: str) -> Optional[Dict]:
        """
        Process a single image and return detection results
        
        Args:
            image_path: Path to image file
            message_id: Telegram message ID
            channel_name: Channel name
            
        Returns:
            Dictionary with detection results or None if error
        """
        logger.debug(f"Processing image: {image_path}")
        
        # Detect objects
        detections = self.detect_objects(image_path)
        
        if not detections:
            logger.debug(f"No detections in {image_path}")
            return {
                'message_id': message_id,
                'channel_name': channel_name,
                'image_path': str(image_path),
                'detected_objects': [],
                'detection_count': 0,
                'image_category': 'other',
                'confidence_score': 0.0,
                'has_person': False,
                'has_product': False
            }
        
        # Classify image
        category, confidence = self.classify_image(detections)
        
        # Extract class names
        class_ids = [d['class_id'] for d in detections]
        has_person = self.PERSON_CLASS in class_ids
        has_product = any(cid in self.PRODUCT_CLASSES for cid in class_ids)
        
        # Get detected object names
        detected_objects = [d['class_name'] for d in detections]
        
        return {
            'message_id': message_id,
            'channel_name': channel_name,
            'image_path': str(image_path),
            'detected_objects': detected_objects,
            'detection_count': len(detections),
            'image_category': category,
            'confidence_score': confidence,
            'has_person': has_person,
            'has_product': has_product,
            'detections_json': json.dumps(detections)  # Full detection details
        }
    
    def scan_and_process_images(self, images_dir: Path, output_csv: Path) -> List[Dict]:
        """
        Scan directory for images and process them
        
        Args:
            images_dir: Base directory containing channel subdirectories
            output_csv: Path to output CSV file
            
        Returns:
            List of all detection results
        """
        logger.info(f"Scanning images in: {images_dir}")
        
        all_results = []
        
        # Find all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
        image_files = []
        
        for channel_dir in images_dir.iterdir():
            if not channel_dir.is_dir():
                continue
            
            channel_name = channel_dir.name
            logger.info(f"Processing channel: {channel_name}")
            
            for image_file in channel_dir.iterdir():
                if image_file.suffix.lower() in image_extensions:
                    # Extract message_id from filename (e.g., "97.jpg" -> 97)
                    try:
                        message_id = int(image_file.stem)
                    except ValueError:
                        logger.warning(f"Could not extract message_id from {image_file.name}, skipping")
                        continue
                    
                    image_files.append((image_file, message_id, channel_name))
        
        logger.info(f"Found {len(image_files)} images to process")
        
        # Process each image
        for idx, (image_file, message_id, channel_name) in enumerate(image_files, 1):
            logger.info(f"Processing [{idx}/{len(image_files)}]: {image_file.name}")
            
            result = self.process_image(image_file, message_id, channel_name)
            if result:
                all_results.append(result)
        
        # Save to CSV
        if all_results:
            self.save_to_csv(all_results, output_csv)
            logger.info(f"Saved {len(all_results)} detection results to {output_csv}")
        
        return all_results
    
    def save_to_csv(self, results: List[Dict], output_path: Path):
        """
        Save detection results to CSV file
        
        Args:
            results: List of detection result dictionaries
            output_path: Path to output CSV file
        """
        if not results:
            logger.warning("No results to save")
            return
        
        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Define CSV columns
        fieldnames = [
            'message_id',
            'channel_name',
            'image_path',
            'detection_count',
            'image_category',
            'confidence_score',
            'has_person',
            'has_product',
            'detected_objects',  # Comma-separated list
            'detections_json'  # Full JSON details
        ]
        
        # Prepare data for CSV (convert lists to strings)
        csv_data = []
        for result in results:
            row = result.copy()
            # Convert detected_objects list to comma-separated string
            if isinstance(row['detected_objects'], list):
                row['detected_objects'] = ','.join(row['detected_objects'])
            csv_data.append(row)
        
        # Write to CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
        
        logger.info(f"Saved {len(csv_data)} rows to {output_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run YOLO object detection on Telegram images")
    parser.add_argument(
        "--images-dir",
        type=str,
        default="data/raw/images",
        help="Directory containing channel subdirectories with images"
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default="data/processed/yolo_detections.csv",
        help="Output CSV file path"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="yolov8n.pt",
        help="YOLO model path"
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.25,
        help="Confidence threshold for detections"
    )
    
    args = parser.parse_args()
    
    # Initialize detector
    detector = YOLODetector(model_path=args.model, confidence_threshold=args.confidence)
    
    # Process images
    images_dir = Path(args.images_dir)
    output_csv = Path(args.output_csv)
    
    results = detector.scan_and_process_images(images_dir, output_csv)
    
    # Print summary
    print("\n" + "=" * 60)
    print("YOLO DETECTION SUMMARY")
    print("=" * 60)
    print(f"Total images processed: {len(results)}")
    
    # Count by category
    categories = {}
    for result in results:
        cat = result['image_category']
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\nImage Categories:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: {count}")
    
    print(f"\nResults saved to: {output_csv}")
