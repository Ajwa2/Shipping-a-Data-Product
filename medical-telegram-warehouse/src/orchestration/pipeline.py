"""
Dagster pipeline for medical telegram warehouse
"""
import asyncio
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from dagster import (
    asset,
    job,
    schedule,
    Definitions,
    DailyPartitionsDefinition,
    AssetExecutionContext,
    Config,
)
from dagster_postgres import PostgresResource

from src.scraper.telegram_scraper import TelegramScraper
from src.loader.postgres_loader import PostgresLoader
from src.enrichment.yolo_enricher import YOLOEnricher


class TelegramScrapeConfig(Config):
    """Configuration for Telegram scraping"""
    channels: str = "@cheMed123,@lobelia4cosmetics,@tikvahpharma"
    limit: int = 1000
    base_path: str = "data"


# PostgreSQL resource
postgres_resource = PostgresResource(
    postgres_connection_string=os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/medical_warehouse")
)


@asset
def scrape_telegram_channels(context: AssetExecutionContext, config: TelegramScrapeConfig) -> Dict[str, Any]:
    """
    Scrape Telegram channels and save to data lake
    
    Returns:
        Dictionary with scraping statistics
    """
    channels = [ch.strip() for ch in config.channels.split(",")]
    base_path = config.base_path
    
    scraper = TelegramScraper(base_path=base_path)
    
    try:
        results = asyncio.run(
            scraper.scrape_channels(channels, limit=config.limit)
        )
        
        total_messages = sum(len(msgs) for msgs in results.values())
        
        stats = {
            "channels_scraped": len(results),
            "total_messages": total_messages,
            "messages_per_channel": {ch: len(msgs) for ch, msgs in results.items()},
            "timestamp": datetime.now().isoformat()
        }
        
        context.log.info(f"Scraped {total_messages} messages from {len(results)} channels")
        return stats
    
    finally:
        asyncio.run(scraper.close())


@asset(deps=[scrape_telegram_channels])
def load_to_postgres(context: AssetExecutionContext, config: TelegramScrapeConfig) -> Dict[str, Any]:
    """
    Load scraped data from data lake to PostgreSQL
    """
    base_path = config.base_path
    today = datetime.now().strftime("%Y-%m-%d")
    
    loader = PostgresLoader()
    loader.create_raw_table()
    
    json_dir = Path(base_path) / "raw" / "telegram_messages" / today
    if json_dir.exists():
        loader.load_from_directory(json_dir)
        count = loader.get_table_count("raw_messages")
        context.log.info(f"Loaded messages to PostgreSQL. Total: {count}")
        
        return {
            "messages_loaded": count,
            "timestamp": datetime.now().isoformat()
        }
    else:
        context.log.warning(f"Data directory not found: {json_dir}")
        return {"messages_loaded": 0, "timestamp": datetime.now().isoformat()}


@asset(deps=[load_to_postgres])
def enrich_with_yolo(context: AssetExecutionContext) -> Dict[str, Any]:
    """
    Enrich images with YOLO object detection
    """
    enricher = YOLOEnricher()
    
    # Create enriched table if needed
    loader = PostgresLoader()
    loader.create_enriched_table()
    loader.close()
    
    # Enrich messages
    enricher.enrich_from_database(limit=1000)
    
    # Get summary
    summary = enricher.get_detection_summary()
    
    context.log.info(f"Enrichment complete. Detected objects: {len(summary)}")
    
    return {
        "enriched_count": len(summary),
        "detection_summary": summary,
        "timestamp": datetime.now().isoformat()
    }


@asset(deps=[enrich_with_yolo])
def run_dbt_models(context: AssetExecutionContext) -> Dict[str, Any]:
    """
    Run dbt transformations
    """
    import subprocess
    import os
    
    dbt_project_dir = Path("medical_warehouse")
    
    if not dbt_project_dir.exists():
        context.log.warning("dbt project directory not found")
        return {"status": "skipped", "reason": "dbt project not found"}
    
    try:
        # Run dbt models
        result = subprocess.run(
            ["dbt", "run", "--project-dir", str(dbt_project_dir)],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if result.returncode == 0:
            context.log.info("dbt models executed successfully")
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }
        else:
            context.log.error(f"dbt run failed: {result.stderr}")
            return {
                "status": "failed",
                "error": result.stderr,
                "timestamp": datetime.now().isoformat()
            }
    
    except FileNotFoundError:
        context.log.warning("dbt command not found. Install dbt-core to run transformations.")
        return {
            "status": "skipped",
            "reason": "dbt not installed",
            "timestamp": datetime.now().isoformat()
        }


@job
def telegram_pipeline():
    """Main pipeline job"""
    scrape_telegram_channels()
    load_to_postgres()
    enrich_with_yolo()
    run_dbt_models()


@schedule(cron_schedule="0 2 * * *", job=telegram_pipeline)
def daily_scrape_schedule():
    """Schedule to run pipeline daily at 2 AM"""
    return {}


# Define repository
defs = Definitions(
    assets=[
        scrape_telegram_channels,
        load_to_postgres,
        enrich_with_yolo,
        run_dbt_models,
    ],
    jobs=[telegram_pipeline],
    schedules=[daily_scrape_schedule],
    resources={"postgres": postgres_resource},
)
