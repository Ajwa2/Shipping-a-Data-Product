# Running the Telegram Scraper

## Quick Start

**IMPORTANT**: You must run this in an **interactive terminal** (not as a background script) so you can enter the verification code.

### Basic Usage

```bash
cd medical-telegram-warehouse
python scripts/scrape_telegram.py
```

### With Options

```bash
# Limit messages per channel
python scripts/scrape_telegram.py --limit 50

# Custom channels
python scripts/scrape_telegram.py @channel1 @channel2
```

## First-Time Setup

1. **Make sure `.env` has your credentials**:
   ```
   TELEGRAM_API_ID=31032379
   TELEGRAM_API_HASH=72c1cf3addb5b443388fb8a21dead14c
   TELEGRAM_PHONE=+251943101449
   ```

2. **Run the scraper** - it will prompt you for:
   - Verification code (check Telegram app)
   - 2FA password (if enabled)

3. **After first run**, a session file is created and you won't need to authenticate again.

## Default Channels

The scraper will automatically scrape:
- `@cheMed123` (CheMed)
- `https://t.me/lobelia4cosmetics` (Lobelia Cosmetics)
- `https://t.me/tikvahpharma` (Tikvah Pharma)

## Output

- **JSON files**: `data/raw/telegram_messages/YYYY-MM-DD/channel_name.json`
- **Images**: `data/raw/images/{channel_name}/{message_id}.jpg`
- **Logs**: `logs/scrape_YYYY-MM-DD.log`

## Next Steps

After scraping:
1. Load data: `python scripts/load_raw_to_postgres.py`
2. Transform: `cd medical_warehouse && dbt run`
3. Explore: Open `notebooks/explore_data_warehouse.ipynb`
