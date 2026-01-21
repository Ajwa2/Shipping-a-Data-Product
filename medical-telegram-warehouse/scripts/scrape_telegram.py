"""
Standalone script to scrape Telegram channels
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.scraper.telegram_scraper import scrape_all_channels

if __name__ == "__main__":
    # Default channels - update as needed
    channels = [
        "@cheMed123",
        "@lobelia4cosmetics",
        "@tikvahpharma"
    ]
    
    # You can also pass channels as command line arguments
    if len(sys.argv) > 1:
        channels = [ch.strip() for ch in sys.argv[1:]]
    
    print(f"Scraping {len(channels)} channels...")
    results = asyncio.run(scrape_all_channels(channels, limit=1000))
    
    total = sum(len(msgs) for msgs in results.values())
    print(f"\nScraped {total} total messages:")
    for channel, messages in results.items():
        print(f"  {channel}: {len(messages)} messages")
