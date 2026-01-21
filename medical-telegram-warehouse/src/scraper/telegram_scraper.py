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
            channel: Channel username (e.g., '@cheMed123' or 'https://t.me/lobelia4cosmetics')
            limit: Maximum number of messages to scrape
            message_delay: Delay between messages in seconds
            
        Returns:
            List of message dictionaries
        """
        # Normalize channel name (handle URLs and @ symbols)
        channel = channel.strip()
        if channel.startswith("https://t.me/"):
            channel = "@" + channel.split("/")[-1]
        if not channel.startswith("@"):
            channel = "@" + channel
        
        channel_name = channel.strip("@")
        today = datetime.now().strftime("%Y-%m-%d")
        
        self.logger.info(f"Starting scrape of {channel} (limit={limit})")
        
        try:
            await self.client.start()
            entity = await self.client.get_entity(channel)
            channel_title = entity.title if hasattr(entity, 'title') else channel_name
            
            self.logger.info(f"Channel found: {channel_title} ({channel_name})")
            
        except ChannelPrivateError:
            error_msg = f"Channel {channel} is private or not accessible"
            self.logger.error(error_msg)
            self.stats["errors"].append({"channel": channel, "error": error_msg})
            return []
        except Exception as e:
            error_msg = f"Error accessing channel {channel}: {str(e)}"
            self.logger.error(error_msg)
            self.stats["errors"].append({"channel": channel, "error": error_msg})
            return []
        
        messages = []
        images_downloaded = 0
        
        # Create image directory: data/raw/images/{channel_name}/
        image_dir = self.base_path / "raw" / "images" / channel_name
        image_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Image directory: {image_dir}")
        
        # Create JSON directory: data/raw/telegram_messages/YYYY-MM-DD/
        json_dir = self.base_path / "raw" / "telegram_messages" / today
        json_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"JSON directory: {json_dir}")
        
        try:
            message_count = 0
            async for message in self.client.iter_messages(entity, limit=limit):
                message_count += 1
                image_path = None
                has_media = message.media is not None
                
                # Download image if present
                # Store as: data/raw/images/{channel_name}/{message_id}.jpg
                if has_media and isinstance(message.media, MessageMediaPhoto):
                    filename = f"{message.id}.jpg"
                    image_path = str(image_dir / filename)
                    try:
                        await self.client.download_media(message.media, image_path)
                        images_downloaded += 1
                        self.logger.debug(f"Downloaded image: {image_path}")
                    except Exception as e:
                        error_msg = f"Failed to download image for message {message.id}: {e}"
                        self.logger.warning(error_msg)
                        image_path = None
                
                # Build message dictionary with all required fields
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
                
                # Log progress every 50 messages
                if message_count % 50 == 0:
                    self.logger.info(f"Scraped {message_count} messages from {channel_name}...")
                
                # Delay between messages to avoid rate limiting
                if message_delay > 0:
                    await asyncio.sleep(message_delay)
        
        except FloodWaitError as e:
            wait_seconds = int(getattr(e, "seconds", 0) or 60)
            error_msg = f"Rate limit hit for {channel}. Waiting {wait_seconds} seconds"
            self.logger.warning(error_msg)
            self.stats["errors"].append({
                "channel": channel,
                "error": "FloodWaitError",
                "wait_seconds": wait_seconds
            })
            await asyncio.sleep(wait_seconds)
            # Log that we hit rate limit but continue with what we have
            self.logger.info(f"Rate limit wait complete. Continuing with {len(messages)} messages collected so far.")
        
        except NetworkError as e:
            error_msg = f"Network error while scraping {channel}: {str(e)}"
            self.logger.error(error_msg)
            self.stats["errors"].append({"channel": channel, "error": error_msg})
            return []
        
        except Exception as e:
            error_msg = f"Unexpected error scraping {channel}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.stats["errors"].append({"channel": channel, "error": error_msg})
            return []
        
        # Save to JSON file: data/raw/telegram_messages/YYYY-MM-DD/channel_name.json
        json_path = json_dir / f"{channel_name}.json"
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
            
            self.logger.info(
                f"Finished scraping {channel_name}: "
                f"{len(messages)} messages, {images_downloaded} images downloaded. "
                f"Saved to {json_path}"
            )
            
            # Update statistics
            self.stats["channels_scraped"].append({
                "channel": channel_name,
                "date": today,
                "messages": len(messages),
                "images": images_downloaded,
                "json_path": str(json_path)
            })
            self.stats["total_messages"] += len(messages)
            self.stats["total_images"] += images_downloaded
            
        except Exception as e:
            error_msg = f"Error saving JSON file for {channel_name}: {str(e)}"
            self.logger.error(error_msg)
            self.stats["errors"].append({"channel": channel, "error": error_msg})
        
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
            channels: List of channel usernames or URLs
            limit: Maximum messages per channel
            channel_delay: Delay between channels in seconds
            
        Returns:
            Dictionary mapping channel names to message lists
        """
        results = {}
        total_channels = len(channels)
        
        self.logger.info(f"Starting scrape of {total_channels} channels")
        self.logger.info(f"Channels: {', '.join(channels)}")
        
        for idx, channel in enumerate(channels, 1):
            self.logger.info(f"[{idx}/{total_channels}] Scraping {channel}...")
            
            messages = await self.scrape_channel(channel, limit=limit)
            channel_name = channel.strip("@").replace("https://t.me/", "")
            results[channel_name] = messages
            
            self.logger.info(
                f"Completed {channel_name}: {len(messages)} messages scraped"
            )
            
            # Delay between channels to avoid rate limiting
            if channel_delay > 0 and idx < total_channels:
                self.logger.info(f"Waiting {channel_delay} seconds before next channel...")
                await asyncio.sleep(channel_delay)
        
        # Log summary
        self._log_summary()
        
        return results
    
    def _log_summary(self):
        """Log scraping summary statistics"""
        self.logger.info("=" * 60)
        self.logger.info("SCRAPING SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Total channels scraped: {len(self.stats['channels_scraped'])}")
        self.logger.info(f"Total messages: {self.stats['total_messages']}")
        self.logger.info(f"Total images downloaded: {self.stats['total_images']}")
        self.logger.info(f"Total errors: {len(self.stats['errors'])}")
        
        if self.stats['channels_scraped']:
            self.logger.info("\nChannels scraped:")
            for ch in self.stats['channels_scraped']:
                self.logger.info(
                    f"  - {ch['channel']} ({ch['date']}): "
                    f"{ch['messages']} messages, {ch['images']} images"
                )
        
        if self.stats['errors']:
            self.logger.warning("\nErrors encountered:")
            for err in self.stats['errors']:
                self.logger.warning(f"  - {err['channel']}: {err['error']}")
        
        self.logger.info("=" * 60)
    
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
    """
    Main entry point for standalone execution
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Telegram Scraper for Ethiopian Medical Channels",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python src/scraper/telegram_scraper.py
    python src/scraper/telegram_scraper.py --limit 500
    python src/scraper/telegram_scraper.py --channels @cheMed123 @lobelia4cosmetics
        """
    )
    parser.add_argument(
        "--channels",
        nargs="+",
        default=[
            "@cheMed123",
            "https://t.me/lobelia4cosmetics",
            "https://t.me/tikvahpharma"
        ],
        help="List of channel usernames or URLs to scrape"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Maximum messages to scrape per channel (default: 1000)"
    )
    parser.add_argument(
        "--message-delay",
        type=float,
        default=1.0,
        help="Delay between messages in seconds (default: 1.0)"
    )
    parser.add_argument(
        "--channel-delay",
        type=float,
        default=3.0,
        help="Delay between channels in seconds (default: 3.0)"
    )
    parser.add_argument(
        "--base-path",
        type=str,
        default="data",
        help="Base directory for data storage (default: data)"
    )
    
    args = parser.parse_args()
    
    # Create scraper and run
    scraper = TelegramScraper(base_path=args.base_path)
    
    try:
        results = asyncio.run(
            scraper.scrape_channels(
                channels=args.channels,
                limit=args.limit,
                channel_delay=args.channel_delay
            )
        )
        
        total = sum(len(msgs) for msgs in results.values())
        print(f"\n✓ Scraping complete: {total} total messages from {len(results)} channels")
        
    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user")
        scraper.logger.warning("Scraping interrupted by user")
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        scraper.logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        asyncio.run(scraper.close())
