"""
Dagster Pipeline for Medical Telegram Warehouse
Task 5 - Pipeline Orchestration

This pipeline orchestrates the entire data pipeline:
1. Scrape Telegram channels
2. Load raw data to PostgreSQL
3. Run dbt transformations
4. Run YOLO enrichment
"""
import asyncio
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from dagster import (
    op,
    job,
    schedule,
    OpExecutionContext,
    DefaultSensorStatus,
    DefaultScheduleStatus,
    sensor,
    SkipReason,
    RunConfig,
    Config,
    Definitions,
)

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.scraper.telegram_scraper import TelegramScraper
from src.loader.postgres_loader import PostgresLoader
from src.enrichment.yolo_detector import YOLODetector


class PipelineConfig(Config):
    """Configuration for the pipeline"""
    channels: str = "@cheMed123,https://t.me/lobelia4cosmetics,https://t.me/tikvahpharma"
    scrape_limit: int = 1000
    base_path: str = "data"
    yolo_confidence: float = 0.25


@op(
    description="Scrape Telegram channels and save data to the data lake"
)
def scrape_telegram_data(context: OpExecutionContext) -> Dict[str, Any]:
    """
    Operation: Scrape Telegram channels
    
    Scrapes messages and images from Telegram channels and saves them
    to the raw data lake (JSON files and images).
    """
    config = PipelineConfig()
    channels_str = config.channels
    limit = config.scrape_limit
    base_path = config.base_path
    
    channels = [ch.strip() for ch in channels_str.split(",")]
    
    context.log.info(f"Starting Telegram scrape for {len(channels)} channels")
    context.log.info(f"Channels: {', '.join(channels)}")
    
    scraper = TelegramScraper(base_path=base_path)
    
    try:
        results = asyncio.run(scraper.scrape_channels(channels, limit=limit))
        
        total_messages = sum(len(msgs) for msgs in results.values())
        total_images = sum(
            len([f for f in (Path(base_path) / "raw" / "images" / ch).glob("*.jpg")])
            for ch in results.keys()
            if (Path(base_path) / "raw" / "images" / ch).exists()
        )
        
        stats = {
            "channels_scraped": len(results),
            "total_messages": total_messages,
            "total_images": total_images,
            "messages_per_channel": {ch: len(msgs) for ch, msgs in results.items()},
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }
        
        context.log.info(f"✓ Scraped {total_messages} messages and {total_images} images from {len(results)} channels")
        
        return stats
        
    except Exception as e:
        context.log.error(f"Error during scraping: {e}")
        raise
    finally:
        asyncio.run(scraper.close())


@op(
    description="Load raw JSON data from data lake to PostgreSQL"
)
def load_raw_to_postgres(context: OpExecutionContext, scrape_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Operation: Load raw data to PostgreSQL
    
    Loads JSON files from the data lake into the raw.telegram_messages table.
    """
    config = PipelineConfig()
    base_path = config.base_path
    today = datetime.now().strftime("%Y-%m-%d")
    
    context.log.info("Loading raw data to PostgreSQL...")
    
    loader = PostgresLoader()
    
    try:
        loader.create_raw_table()
        
        json_dir = Path(base_path) / "raw" / "telegram_messages" / today
        if not json_dir.exists():
            # Try to find any available date directory
            base_json_dir = Path(base_path) / "raw" / "telegram_messages"
            if base_json_dir.exists():
                date_dirs = sorted([d for d in base_json_dir.iterdir() if d.is_dir()], reverse=True)
                if date_dirs:
                    json_dir = date_dirs[0]
                    context.log.info(f"Using data from: {json_dir.name}")
        
        if json_dir.exists():
            loader.load_from_directory(json_dir)
            count = loader.get_table_count("raw.telegram_messages")
            
            context.log.info(f"✓ Loaded {count} messages to raw.telegram_messages")
            
            return {
                "messages_loaded": count,
                "data_directory": str(json_dir),
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
        else:
            context.log.warning(f"Data directory not found: {json_dir}")
            return {
                "messages_loaded": 0,
                "data_directory": None,
                "timestamp": datetime.now().isoformat(),
                "status": "skipped"
            }
    except Exception as e:
        context.log.error(f"Error loading data: {e}")
        raise
    finally:
        loader.close()


@op(
    description="Run dbt transformations to build data warehouse"
)
def run_dbt_transformations(context: OpExecutionContext, load_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Operation: Run dbt transformations
    
    Executes dbt models to transform raw data into the dimensional data warehouse.
    """
    context.log.info("Running dbt transformations...")
    
    dbt_project_dir = project_root / "medical_warehouse"
    
    if not dbt_project_dir.exists():
        context.log.warning("dbt project directory not found")
        return {
            "status": "skipped",
            "reason": "dbt project not found",
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        # Change to dbt project directory
        original_cwd = os.getcwd()
        os.chdir(dbt_project_dir)
        
        # Run dbt deps first (if needed)
        try:
            deps_result = subprocess.run(
                ["dbt", "deps"],
                capture_output=True,
                text=True,
                timeout=300
            )
            if deps_result.returncode != 0:
                context.log.warning(f"dbt deps had warnings: {deps_result.stderr}")
        except Exception as e:
            context.log.warning(f"dbt deps skipped: {e}")
        
        # Run dbt models
        result = subprocess.run(
            ["dbt", "run"],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        os.chdir(original_cwd)
        
        if result.returncode == 0:
            context.log.info("✓ dbt transformations completed successfully")
            # Log summary
            output_lines = result.stdout.split('\n')
            summary_lines = [line for line in output_lines if 'PASS' in line or 'SELECT' in line or 'CREATE' in line]
            if summary_lines:
                context.log.info("\n".join(summary_lines[-10:]))  # Last 10 relevant lines
            
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }
        else:
            error_msg = result.stderr or result.stdout
            context.log.error(f"✗ dbt run failed: {error_msg[-500:]}")
            raise Exception(f"dbt run failed: {error_msg[-500:]}")
    
    except FileNotFoundError:
        context.log.warning("dbt command not found. Install dbt-postgres to run transformations.")
        return {
            "status": "skipped",
            "reason": "dbt not installed",
            "timestamp": datetime.now().isoformat()
        }
    except subprocess.TimeoutExpired:
        context.log.error("dbt run timed out")
        raise
    except Exception as e:
        context.log.error(f"Error running dbt: {e}")
        raise
    finally:
        if 'original_cwd' in locals():
            os.chdir(original_cwd)


@op(
    description="Run YOLO object detection on images"
)
def run_yolo_enrichment(context: OpExecutionContext, dbt_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Operation: Run YOLO enrichment
    
    Processes images with YOLO object detection and saves results to CSV,
    then loads to PostgreSQL.
    """
    config = PipelineConfig()
    base_path = config.base_path
    confidence = config.yolo_confidence
    
    context.log.info("Running YOLO object detection...")
    
    images_dir = Path(base_path) / "raw" / "images"
    output_csv = Path(base_path) / "processed" / "yolo_detections.csv"
    
    if not images_dir.exists():
        context.log.warning(f"Images directory not found: {images_dir}")
        return {
            "status": "skipped",
            "reason": "No images directory",
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        # Create output directory
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize detector
        detector = YOLODetector(model_path="yolov8n.pt", confidence_threshold=confidence)
        
        # Process images
        results = detector.scan_and_process_images(images_dir, output_csv)
        
        # Load to PostgreSQL
        from scripts.load_yolo_to_postgres import load_yolo_results
        from dotenv import load_dotenv
        load_dotenv()
        
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            load_yolo_results(output_csv, database_url)
            context.log.info(f"✓ Loaded YOLO results to PostgreSQL")
        else:
            context.log.warning("DATABASE_URL not set, skipping database load")
        
        # Count by category
        categories = {}
        for result in results:
            cat = result['image_category']
            categories[cat] = categories.get(cat, 0) + 1
        
        context.log.info(f"✓ Processed {len(results)} images")
        context.log.info(f"  Categories: {categories}")
        
        return {
            "status": "success",
            "images_processed": len(results),
            "categories": categories,
            "output_csv": str(output_csv),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        context.log.error(f"Error during YOLO enrichment: {e}")
        raise


@job(
    description="Complete data pipeline: Scrape → Load → Transform → Enrich"
)
def medical_telegram_pipeline():
    """
    Main pipeline job that orchestrates all operations in sequence:
    1. Scrape Telegram data
    2. Load to PostgreSQL
    3. Run dbt transformations
    4. Run YOLO enrichment
    """
    scrape_result = scrape_telegram_data()
    load_result = load_raw_to_postgres(scrape_result)
    dbt_result = run_dbt_transformations(load_result)
    run_yolo_enrichment(dbt_result)


@schedule(
    cron_schedule="0 2 * * *",  # Daily at 2 AM
    job=medical_telegram_pipeline,
    default_status=DefaultScheduleStatus.STOPPED,  # Start as stopped, enable manually
    description="Daily pipeline run at 2 AM"
)
def daily_pipeline_schedule(context):
    """Schedule to run the pipeline daily at 2 AM"""
    return RunConfig()


@sensor(
    job=medical_telegram_pipeline,
    default_status=DefaultSensorStatus.STOPPED,
    description="Manual trigger sensor for pipeline"
)
def manual_pipeline_sensor(context):
    """Sensor for manually triggering the pipeline"""
    # This sensor can be triggered manually from the UI
    return SkipReason("Manual trigger only - use Dagster UI to run")


# Define the repository
defs = Definitions(
    jobs=[medical_telegram_pipeline],
    schedules=[daily_pipeline_schedule],
    sensors=[manual_pipeline_sensor],
)
