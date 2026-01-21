"""
Telegram Scraper for Ethiopian Medical Channels
================================================
This script scrapes public Telegram channels and stores:
- Raw messages as JSON (partitioned by date): data/raw/telegram_messages/YYYY-MM-DD/channel_name.json
- Images: data/raw/images/{channel_name}/{message_id}.jpg
- Logs: logs/scrape_YYYY-MM-DD.log

Usage:
    python src/scraper/telegram_scraper.py
    or
    from src.scraper.telegram_scraper import TelegramScraper
    scraper = TelegramScraper()
    await scraper.scrape_channels(["@cheMed123", "@lobelia4cosmetics", "@tikvahpharma"])
"""
import asyncio
import os
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from telethon import TelegramClient
from telethon.errors import FloodWaitError, NetworkError, ChannelPrivateError
from telethon.tl.types import MessageMediaPhoto
from dotenv import load_dotenv

load_dotenv()

# Date string for partitioning output files
TODAY = datetime.now().strftime("%Y-%m-%d")


class TelegramScraper:
    """Scraper for Telegram channels"""
    
    def __init__(self, base_path: str = "data"):
        self.base_path = Path(base_path)
        self.api_id = int(os.getenv("TELEGRAM_API_ID", "0"))
        self.api_hash = os.getenv("TELEGRAM_API_HASH", "")
        self.client = TelegramClient("telegram_scraper_session", self.api_id, self.api_hash)
        
        if not self.api_id or not self.api_hash:
            raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env")
        
        # Setup logging
        self._setup_logging()
        
        # Track scraping statistics
        self.stats = {
            "channels_scraped": [],
            "total_messages": 0,
            "total_images": 0,
            "errors": []
        }
    
    def _setup_logging(self):
        """Setup logging to file and console"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger("telegram_scraper")
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers = []
        
        # File handler - logs everything to file
        log_file = log_dir / f"scrape_{TODAY}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        
        # Console handler - shows progress in terminal
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            logging.Formatter("%(levelname)s: %(message)s")
        )
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info(f"Logging initialized. Log file: {log_file}")
    
    async def scrape_channel(
        self, 
        channel: str, 
        limit: int = 1000,
        message_delay: float = 1.0
    ) -> List[Dict[str, Any]]:
        """
        Scrape messages from a Telegram channel
        
        Args:
            channel: Channel username (e.g., '@cheMed123')
            limit: Maximum number of messages to scrape
            message_delay: Delay between messages in seconds
            
        Returns:
            List of message dictionaries
        """
        await self.client.start()
        entity = await self.client.get_entity(channel)
        channel_name = channel.strip("@")
        channel_title = entity.title if hasattr(entity, 'title') else channel_name
        
        messages = []
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Create image directory
        image_dir = self.base_path / "raw" / "images" / channel_name
        image_dir.mkdir(parents=True, exist_ok=True)
        
        # Create JSON directory
        json_dir = self.base_path / "raw" / "telegram_messages" / today
        json_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            async for message in self.client.iter_messages(entity, limit=limit):
                image_path = None
                has_media = message.media is not None
                
                # Download image if present
                if has_media and isinstance(message.media, MessageMediaPhoto):
                    filename = f"{message.id}.jpg"
                    image_path = str(image_dir / filename)
                    try:
                        await self.client.download_media(message.media, image_path)
                    except Exception as e:
                        print(f"Failed to download image for message {message.id}: {e}")
                        image_path = None
                
                # Build message dictionary
                msg_dict = {
                    "message_id": message.id,
                    "channel_name": channel_name,
                    "channel_title": channel_title,
                    "message_date": message.date.isoformat() if message.date else None,
                    "message_text": message.message or "",
                    "has_media": has_media,
                    "image_path": image_path,
                    "views": message.views or 0,
                    "forwards": message.forwards or 0,
                }
                messages.append(msg_dict)
                
                # Delay between messages
                if message_delay > 0:
                    await asyncio.sleep(message_delay)
        
        except FloodWaitError as e:
            wait_seconds = int(getattr(e, "seconds", 0) or 60)
            print(f"FloodWaitError: waiting {wait_seconds} seconds")
            await asyncio.sleep(wait_seconds)
        except Exception as e:
            print(f"Error scraping {channel}: {e}")
        
        # Save to JSON file
        json_path = json_dir / f"{channel_name}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
        
        return messages
    
    async def scrape_channels(
        self,
        channels: List[str],
        limit: int = 1000,
        channel_delay: float = 3.0
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Scrape multiple Telegram channels
        
        Args:
            channels: List of channel usernames
            limit: Maximum messages per channel
            channel_delay: Delay between channels in seconds
            
        Returns:
            Dictionary mapping channel names to message lists
        """
        results = {}
        
        for channel in channels:
            print(f"Scraping {channel}...")
            messages = await self.scrape_channel(channel, limit=limit)
            results[channel.strip("@")] = messages
            print(f"Scraped {len(messages)} messages from {channel}")
            
            if channel_delay > 0:
                await asyncio.sleep(channel_delay)
        
        return results
    
    async def close(self):
        """Close the Telegram client"""
        await self.client.disconnect()


async def scrape_all_channels(
    channels: List[str],
    base_path: str = "data",
    limit: int = 1000
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Convenience function to scrape all channels
    
    Args:
        channels: List of channel usernames
        base_path: Base directory for data storage
        limit: Maximum messages per channel
        
    Returns:
        Dictionary mapping channel names to message lists
    """
    scraper = TelegramScraper(base_path=base_path)
    try:
        results = await scraper.scrape_channels(channels, limit=limit)
        return results
    finally:
        await scraper.close()


if __name__ == "__main__":
    # Example usage
    channels = [
        "@cheMed123",
        "@lobelia4cosmetics",
        "@tikvahpharma"
    ]
    
    results = asyncio.run(scrape_all_channels(channels, limit=100))
    print(f"Scraped {sum(len(msgs) for msgs in results.values())} total messages")
