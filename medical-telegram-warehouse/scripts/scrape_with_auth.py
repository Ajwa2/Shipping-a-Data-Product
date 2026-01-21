"""
Interactive scraper that handles Telegram authentication properly
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.scraper.telegram_scraper import TelegramScraper

if __name__ == "__main__":
    # Default channels
    channels = [
        "@cheMed123",
        "https://t.me/lobelia4cosmetics",
        "https://t.me/tikvahpharma"
    ]
    
    print("=" * 60)
    print("Task 1: Data Scraping and Collection")
    print("=" * 60)
    print(f"Channels to scrape: {len(channels)}")
    for ch in channels:
        print(f"  - {ch}")
    print()
    print("Note: On first run, you'll need to:")
    print("  1. Enter your phone number (or press Enter to use from .env)")
    print("  2. Enter verification code from Telegram app")
    print("  3. Enter 2FA password if enabled")
    print()
    
    scraper = TelegramScraper()
    
    try:
        # Start client interactively for first-time auth
        import os
        from dotenv import load_dotenv
        load_dotenv()
        phone = os.getenv("TELEGRAM_PHONE", "")
        
        if phone:
            print(f"Using phone number from .env: {phone}")
        else:
            print("No phone number in .env - you'll be prompted")
        
        # Start the client (will prompt if needed)
        asyncio.run(scraper.client.start(phone=phone if phone else None))
        
        # Now scrape
        results = asyncio.run(scraper.scrape_channels(channels, limit=100))
        
        total = sum(len(msgs) for msgs in results.values())
        print(f"\n[SUCCESS] Task 1 Complete!")
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
        import traceback
        traceback.print_exc()
    finally:
        asyncio.run(scraper.close())
