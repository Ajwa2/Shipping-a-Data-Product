# How to Run the Telegram Scraper

## Important: First-Time Authentication

On the **first run only**, Telegram will ask you to:
1. Enter your phone number (or press Enter to use from .env)
2. Enter the verification code sent to your Telegram app
3. Enter your 2FA password (if you have 2FA enabled)

After the first authentication, a session file will be saved and you won't need to authenticate again.

## Step-by-Step Instructions

### Step 1: Open Terminal/Command Prompt

Make sure you're in an **interactive terminal** (not running as a background script) so you can enter the verification code.

### Step 2: Run the Scraper

```bash
cd medical-telegram-warehouse
python scripts/scrape_telegram.py
```

Or with a limit:
```bash
python scripts/scrape_telegram.py --limit 100
```

### Step 3: First-Time Authentication

When you run it for the first time, you'll see:

```
Please enter your phone (or bot token): 
```

**Option A**: Press Enter to use the phone number from your `.env` file (+251943101449)

**Option B**: Type your phone number manually

Then you'll see:
```
Please enter the code you received: 
```

1. Check your Telegram app
2. You'll see a message like "Login code: 12345"
3. Enter that code in the terminal
4. Press Enter

If you have 2FA enabled:
```
Please enter your password: 
```
Enter your 2FA password and press Enter.

### Step 4: Scraping Starts

After authentication, the scraper will:
- Connect to Telegram
- Scrape messages from the channels
- Download images
- Save data to `data/raw/telegram_messages/`

### Step 5: Check Results

After scraping completes, check:
- JSON files: `data/raw/telegram_messages/YYYY-MM-DD/`
- Images: `data/raw/images/{channel_name}/`
- Logs: `logs/scrape_YYYY-MM-DD.log`

## Troubleshooting

### "EOF when reading a line"
- You're running in a non-interactive environment
- Run the script in a regular terminal/command prompt
- Don't run it as a background process

### "Phone number invalid"
- Make sure it's in international format: `+251943101449`
- Include the `+` sign

### "Invalid code"
- Codes expire quickly (usually 5 minutes)
- Request a new code and try again

### "Channel is private"
- Some channels may require you to join them first
- Join the channel in Telegram app, then try scraping again

## After Scraping

Once you have data:

1. **Load to PostgreSQL**:
   ```bash
   python scripts/load_raw_to_postgres.py
   ```

2. **Run dbt transformations**:
   ```bash
   cd medical_warehouse
   dbt run
   ```

3. **View in notebook**:
   - Open `notebooks/explore_data_warehouse.ipynb`
   - Run all cells to see your data!

## Session File

After first authentication, a file like `telegram_scraper_251943101449.session` will be created. This stores your authentication, so you won't need to enter the code again.

**Important**: Don't delete this file, or you'll need to authenticate again!
