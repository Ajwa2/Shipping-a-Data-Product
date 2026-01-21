# Task 1 - Data Scraping and Collection Guide

## Overview
This guide will help you complete Task 1: Building a data scraping pipeline that extracts messages and images from Telegram channels and stores them in a raw data lake.

## Prerequisites

### 1. Set Up Telegram API Access

1. Go to https://my.telegram.org/apps
2. Log in with your phone number
3. Create a new application
4. Note down your `api_id` and `api_hash`

### 2. Configure Environment Variables

Create or update your `.env` file in the project root:

```bash
# Telegram API Credentials
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_PHONE=your_phone_number_here  # Optional, for first-time auth
```

**Important**: Never commit your `.env` file to git!

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `telethon` - Telegram API client
- Other required dependencies

## Running the Scraper

### Option 1: Using the Standalone Script (Recommended)

```bash
# Use default channels
python scripts/scrape_telegram.py

# Specify custom channels
python scripts/scrape_telegram.py @cheMed123 https://t.me/lobelia4cosmetics

# Limit messages per channel
python scripts/scrape_telegram.py --limit 500
```

### Option 2: Using the Module Directly

```bash
# From project root
python src/scraper/telegram_scraper.py --channels @cheMed123 @lobelia4cosmetics --limit 1000
```

### Option 3: Using Python Code

```python
from src.scraper.telegram_scraper import TelegramScraper
import asyncio

scraper = TelegramScraper()

channels = [
    "@cheMed123",
    "https://t.me/lobelia4cosmetics",
    "https://t.me/tikvahpharma"
]

results = asyncio.run(scraper.scrape_channels(channels, limit=1000))
asyncio.run(scraper.close())
```

## First-Time Authentication

On the first run, Telegram will ask you to:
1. Enter your phone number
2. Enter the verification code sent to your Telegram app
3. Enter your 2FA password (if enabled)

After authentication, a session file (`telegram_scraper_session.session`) will be created. You won't need to authenticate again unless you delete this file.

## Data Structure

The scraper creates the following structure:

```
data/
├── raw/
│   ├── telegram_messages/
│   │   └── YYYY-MM-DD/
│   │       ├── cheMed123.json
│   │       ├── lobelia4cosmetics.json
│   │       └── tikvahpharma.json
│   └── images/
│       ├── cheMed123/
│       │   ├── 12345.jpg
│       │   ├── 12346.jpg
│       │   └── ...
│       ├── lobelia4cosmetics/
│       │   └── ...
│       └── tikvahpharma/
│           └── ...
logs/
└── scrape_YYYY-MM-DD.log
```

## Data Fields Collected

Each message JSON contains:

```json
{
  "message_id": 12345,
  "channel_name": "cheMed123",
  "channel_title": "CheMed",
  "message_date": "2024-01-15T10:30:00+00:00",
  "message_text": "Product description...",
  "has_media": true,
  "image_path": "data/raw/images/cheMed123/12345.jpg",
  "views": 150,
  "forwards": 5
}
```

## Logging

Logs are stored in `logs/scrape_YYYY-MM-DD.log` and include:

- Which channels were scraped
- Dates of scraping
- Number of messages and images per channel
- Errors (rate limiting, network issues, etc.)
- Summary statistics

### Example Log Output

```
INFO: Starting scrape of @cheMed123 (limit=1000)
INFO: Channel found: CheMed (cheMed123)
INFO: Image directory: data/raw/images/cheMed123
INFO: JSON directory: data/raw/telegram_messages/2024-01-15
INFO: Scraped 50 messages from cheMed123...
INFO: Finished scraping cheMed123: 1000 messages, 450 images downloaded
INFO: ============================================================
INFO: SCRAPING SUMMARY
INFO: ============================================================
INFO: Total channels scraped: 3
INFO: Total messages: 3000
INFO: Total images downloaded: 1200
INFO: Total errors: 0
```

## Error Handling

The scraper handles common errors:

1. **Rate Limiting (FloodWaitError)**: Automatically waits and retries
2. **Network Errors**: Logs and continues with next channel
3. **Private Channels**: Logs error and skips
4. **Image Download Failures**: Logs warning but continues

## Finding More Channels

Visit https://et.tgstat.com/medicine to find additional Ethiopian medical Telegram channels.

Add them to your channel list:

```bash
python scripts/scrape_telegram.py @channel1 @channel2 @channel3
```

## Troubleshooting

### "Missing TELEGRAM_API_ID or TELEGRAM_API_HASH"
- Check your `.env` file exists and has the correct variables
- Ensure variable names match exactly (case-sensitive)

### "Channel is private or not accessible"
- Some channels may be private or require membership
- Try joining the channel first, then scraping

### "Rate limit hit"
- The scraper automatically handles this by waiting
- Reduce `--limit` or increase delays if this happens frequently

### "Network error"
- Check your internet connection
- Telegram may be blocked in some regions (use VPN if needed)

## Verification

After scraping, verify your data:

1. **Check JSON files exist**:
   ```bash
   ls data/raw/telegram_messages/$(date +%Y-%m-%d)/
   ```

2. **Check images downloaded**:
   ```bash
   ls data/raw/images/cheMed123/ | head -10
   ```

3. **Check logs**:
   ```bash
   tail -50 logs/scrape_$(date +%Y-%m-%d).log
   ```

4. **Verify data structure**:
   ```python
   import json
   with open('data/raw/telegram_messages/2024-01-15/cheMed123.json') as f:
       data = json.load(f)
       print(f"Messages: {len(data)}")
       print(f"Sample: {data[0]}")
   ```

## Deliverables Checklist

- [x] Working scraper script (`src/scraper/telegram_scraper.py`)
- [x] Raw JSON files in `data/raw/telegram_messages/YYYY-MM-DD/channel_name.json`
- [x] Downloaded images in `data/raw/images/{channel_name}/{message_id}.jpg`
- [x] Log files in `logs/scrape_YYYY-MM-DD.log`
- [x] All required fields collected (message_id, date, text, views, forwards, media)
- [x] Error handling and logging implemented

## Next Steps

After completing Task 1, proceed to:
- **Task 2**: Load data from data lake to PostgreSQL
- **Task 3**: Transform data with dbt
- **Task 4**: Enrich with YOLO
- **Task 5**: Build analytical API
