"""
Script to run YOLO object detection on all scraped images
Task 3 - Data Enrichment
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.enrichment.yolo_detector import YOLODetector

if __name__ == "__main__":
    print("=" * 60)
    print("Task 3: Data Enrichment with Object Detection (YOLO)")
    print("=" * 60)
    print()
    
    # Paths
    images_dir = project_root / "data" / "raw" / "images"
    output_csv = project_root / "data" / "processed" / "yolo_detections.csv"
    
    # Create output directory
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Images directory: {images_dir}")
    print(f"Output CSV: {output_csv}")
    print()
    
    # Initialize detector with YOLOv8 nano model
    print("Loading YOLOv8 nano model...")
    detector = YOLODetector(model_path="yolov8n.pt", confidence_threshold=0.25)
    
    # Process all images
    print("\nProcessing images...")
    results = detector.scan_and_process_images(images_dir, output_csv)
    
    # Print summary
    print("\n" + "=" * 60)
    print("DETECTION COMPLETE")
    print("=" * 60)
    print(f"Total images processed: {len(results)}")
    
    if results:
        # Count by category
        categories = {}
        total_detections = 0
        for result in results:
            cat = result['image_category']
            categories[cat] = categories.get(cat, 0) + 1
            total_detections += result['detection_count']
        
        print(f"Total objects detected: {total_detections}")
        print("\nImage Categories:")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(results)) * 100
            print(f"  {cat:20s}: {count:3d} ({percentage:5.1f}%)")
        
        print(f"\n[SUCCESS] Results saved to: {output_csv}")
        print("\nNext steps:")
        print("  1. Load to PostgreSQL: python scripts/load_yolo_to_postgres.py")
        print("  2. Run dbt: cd medical_warehouse && dbt run --select fct_image_detections")
    else:
        print("\n[WARNING] No images were processed. Check that images exist in:")
        print(f"  {images_dir}")
