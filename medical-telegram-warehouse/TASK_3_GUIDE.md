# Task 3 - Data Enrichment with Object Detection (YOLO)

## Overview

This task enriches the data warehouse with computer vision insights using YOLOv8 object detection. Images are analyzed to detect objects (people, products, etc.) and classified into categories for analytical insights.

## Implementation

### 1. YOLO Detection Script (`src/enrichment/yolo_detector.py`)

- Uses YOLOv8 nano model (`yolov8n.pt`) for efficient detection
- Scans images from `data/raw/images/{channel_name}/`
- Detects objects with confidence scores
- Classifies images into categories:
  - **promotional**: Person + product (someone showing/holding item)
  - **product_display**: Bottle/container, no person
  - **lifestyle**: Person, no product
  - **other**: Neither detected

### 2. Data Flow

1. **Run YOLO Detection**:
   ```bash
   python scripts/run_yolo_detection.py
   ```
   - Processes all images in `data/raw/images/`
   - Saves results to `data/processed/yolo_detections.csv`

2. **Load to PostgreSQL**:
   ```bash
   python scripts/load_yolo_to_postgres.py
   ```
   - Creates `raw.enriched_messages` table
   - Loads detection results from CSV

3. **Transform with dbt**:
   ```bash
   cd medical_warehouse
   dbt run --select fct_image_detections
   ```
   - Creates `fct_image_detections` fact table
   - Joins YOLO results with `fct_messages` for analysis

4. **Analyze Results**:
   ```bash
   python scripts/analyze_image_content.py
   ```
   - Answers business questions about image content patterns

## Business Questions Answered

### Q1: Do "promotional" posts get more views than "product_display" posts?
- Compares average views between promotional (person+product) and product_display (product only) posts
- Shows engagement differences by image content type

### Q2: Which channels use more visual content?
- Analyzes detection coverage across channels
- Shows which channels have more images with detectable objects

### Q3: Limitations of pre-trained models
- Identifies limitations of using general-purpose YOLO for domain-specific medical product detection
- Shows confidence scores and detection patterns

## Files Created

- `src/enrichment/yolo_detector.py` - YOLO detection and classification logic
- `scripts/run_yolo_detection.py` - Script to run detection on all images
- `scripts/load_yolo_to_postgres.py` - Load detection results to database
- `scripts/analyze_image_content.py` - Business questions analysis
- `medical_warehouse/models/marts/fct_image_detections.sql` - dbt model for image detections

## Output

- **CSV**: `data/processed/yolo_detections.csv` - Detection results
- **PostgreSQL**: `raw.enriched_messages` - Raw detection data
- **dbt Model**: `fct_image_detections` - Integrated fact table for analysis

## Next Steps

After running the detection:
1. Review detection results in CSV
2. Load to database
3. Run dbt transformations
4. Analyze patterns with the analysis script
5. Use insights in your report
