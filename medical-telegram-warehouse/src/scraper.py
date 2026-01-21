"""
Main scraper script for Task 1 - Data Scraping and Collection
This is a convenience wrapper that can be run directly.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import and run the scraper
if __name__ == "__main__":
    from src.scraper.telegram_scraper import TelegramScraper
    import asyncio
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Telegram Scraper for Ethiopian Medical Channels - Task 1"
    )
    parser.add_argument(
        "--channels",
        nargs="+",
        default=[
            "@cheMed123",
            "https://t.me/lobelia4cosmetics",
            "https://t.me/tikvahpharma"
        ],
        help="List of channel usernames or URLs"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Maximum messages per channel"
    )
    parser.add_argument(
        "--base-path",
        type=str,
        default="data",
        help="Base directory for data storage"
    )
    
    args = parser.parse_args()
    
    scraper = TelegramScraper(base_path=args.base_path)
    
    try:
        results = asyncio.run(
            scraper.scrape_channels(channels=args.channels, limit=args.limit)
        )
        print(f"\n✓ Task 1 Complete: Scraped {sum(len(msgs) for msgs in results.values())} messages")
    finally:
        asyncio.run(scraper.close())
