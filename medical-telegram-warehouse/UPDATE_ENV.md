# Update Your .env File

You have successfully created your Telegram API application! 

## Your Credentials:
- **api_id**: `31032379`
- **api_hash**: `72c1cf3addb5b443388fb8a21dead14c`

## Steps to Add Credentials:

1. Open the `.env` file in the `medical-telegram-warehouse` folder

2. Find these lines:
   ```
   TELEGRAM_API_ID=your_api_id_here
   TELEGRAM_API_HASH=your_api_hash_here
   ```

3. Replace them with:
   ```
   TELEGRAM_API_ID=31032379
   TELEGRAM_API_HASH=72c1cf3addb5b443388fb8a21dead14c
   ```

4. Add your phone number (the one you used to log in):
   ```
   TELEGRAM_PHONE=+251XXXXXXXXX
   ```
   (Replace with your actual phone number with country code)

5. Save the file

## After Updating .env:

Run the scraper:
```bash
python scripts/scrape_telegram.py --limit 100
```

This will scrape 100 messages from each channel.
