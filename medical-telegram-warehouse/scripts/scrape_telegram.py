"""
Standalone script to scrape Telegram channels
Task 1 - Data Scraping and Collection
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.scraper.telegram_scraper import TelegramScraper

if __name__ == "__main__":
    # Default channels from requirements
    # CheMed, Lobelia Cosmetics, Tikvah Pharma
    channels = [
        "@cheMed123",
        "https://t.me/lobelia4cosmetics",
        "https://t.me/tikvahpharma"
    ]
    
    # You can also pass channels as command line arguments
    if len(sys.argv) > 1:
        channels = [ch.strip() for ch in sys.argv[1:]]
    
    print("=" * 60)
    print("Task 1: Data Scraping and Collection")
    print("=" * 60)
    print(f"Channels to scrape: {len(channels)}")
    for ch in channels:
        print(f"  - {ch}")
    print()
    
    scraper = TelegramScraper()
    
    try:
        results = asyncio.run(scraper.scrape_channels(channels, limit=1000))
        
        total = sum(len(msgs) for msgs in results.values())
        print(f"\n✓ Task 1 Complete!")
        print(f"  Total messages scraped: {total}")
        print(f"  Channels processed: {len(results)}")
        print("\nData saved to:")
        print("  - JSON: data/raw/telegram_messages/YYYY-MM-DD/channel_name.json")
        print("  - Images: data/raw/images/{channel_name}/{message_id}.jpg")
        print("  - Logs: logs/scrape_YYYY-MM-DD.log")
        
    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
    finally:
        asyncio.run(scraper.close())
