# Task 5 - Pipeline Orchestration with Dagster

## Overview

This task automates the entire data pipeline using Dagster, an orchestration tool that provides:
- **Observability**: Monitor pipeline execution and logs
- **Scheduling**: Run pipelines automatically on a schedule
- **Dependency Management**: Ensure operations run in the correct order
- **Error Handling**: Track failures and retries

## Pipeline Operations

The pipeline consists of 4 operations executed in sequence:

1. **scrape_telegram_data**
   - Scrapes messages and images from Telegram channels
   - Saves data to raw data lake (JSON files and images)
   - Returns statistics about scraped data

2. **load_raw_to_postgres**
   - Loads JSON files from data lake to PostgreSQL
   - Creates/updates `raw.telegram_messages` table
   - Depends on: `scrape_telegram_data`

3. **run_dbt_transformations**
   - Executes dbt models to build data warehouse
   - Creates staging, dimension, and fact tables
   - Depends on: `load_raw_to_postgres`

4. **run_yolo_enrichment**
   - Runs YOLO object detection on images
   - Saves results to CSV and loads to PostgreSQL
   - Depends on: `run_dbt_transformations`

## Running the Pipeline

### Option 1: Using Dagster Dev Server (Recommended)

```bash
cd medical-telegram-warehouse
python scripts/run_dagster.py
```

Or directly:
```bash
dagster dev -f pipeline.py
```

Then access the Dagster UI at: **http://localhost:3000**

### Option 2: Using Dagster CLI

```bash
# Run the pipeline
dagster job execute -f pipeline.py -j medical_telegram_pipeline

# Launch UI
dagster dev -f pipeline.py
```

## Using the Dagster UI

1. **Access the UI**: Open http://localhost:3000 in your browser

2. **View Jobs**: Click on "Jobs" in the left sidebar
   - You'll see `medical_telegram_pipeline`

3. **Run the Pipeline**:
   - Click on the job name
   - Click "Launch Run" button
   - Monitor execution in real-time

4. **View Execution**:
   - See operation status (success/failure)
   - View logs for each operation
   - See execution graph showing dependencies

5. **Monitor Schedules**:
   - Go to "Schedules" in the sidebar
   - Enable/disable the daily schedule
   - View schedule history

## Pipeline Configuration

The pipeline uses default configuration in `PipelineConfig`:
- **channels**: "@cheMed123,https://t.me/lobelia4cosmetics,https://t.me/tikvahpharma"
- **scrape_limit**: 1000 messages per channel
- **base_path**: "data"
- **yolo_confidence**: 0.25

You can override these in the Dagster UI when launching a run.

## Scheduling

The pipeline includes a daily schedule that runs at 2 AM:

```python
@schedule(
    cron_schedule="0 2 * * *",  # Daily at 2 AM
    job=medical_telegram_pipeline
)
```

To enable the schedule:
1. Go to "Schedules" in Dagster UI
2. Find "daily_pipeline_schedule"
3. Click "Toggle On"

## Error Handling

Dagster provides built-in error handling:
- **Failed operations** are clearly marked in the UI
- **Logs** show detailed error messages
- **Retries** can be configured
- **Alerts** can be set up for failures

## Pipeline Graph

The execution graph shows dependencies:
```
scrape_telegram_data
    ↓
load_raw_to_postgres
    ↓
run_dbt_transformations
    ↓
run_yolo_enrichment
```

Each operation waits for the previous one to complete successfully.

## Files Created

- `src/orchestration/pipeline.py` - Pipeline definition with ops
- `pipeline.py` - Main entry point for Dagster
- `scripts/run_dagster.py` - Script to launch Dagster dev server
- `TASK_5_GUIDE.md` - This guide

## Troubleshooting

### "Dagster not found"
```bash
pip install dagster dagster-webserver
```

### "Port 3000 already in use"
Change the port:
```bash
dagster dev -f pipeline.py --port 3001
```

### "Operation failed"
- Check logs in Dagster UI
- Verify database connection
- Ensure all dependencies are installed
- Check that data directories exist

### "dbt command not found"
```bash
pip install dbt-postgres
```

## Next Steps

1. **Run the pipeline** using Dagster UI
2. **Take screenshots** of:
   - Dagster UI showing the job graph
   - Successful pipeline execution
   - Operation logs
   - Schedule configuration
3. **Enable scheduling** if desired
4. **Set up alerts** for production use

## Production Considerations

For production deployment:
- Use Dagster Cloud or self-hosted Dagster
- Configure proper error notifications
- Set up monitoring and alerting
- Use secrets management for API keys
- Configure resource limits
- Set up backup and recovery
