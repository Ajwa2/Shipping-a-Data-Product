# Running Notebook Analysis

## Quick Start

The script `run_notebook_analysis.py` executes all notebook cells and shows the output in the terminal.

### Prerequisites

1. **Start PostgreSQL**:
   ```bash
   cd medical-telegram-warehouse
   docker-compose up -d
   ```

2. **Load Data** (if not already done):
   ```bash
   python scripts/load_raw_to_postgres.py
   ```

3. **Run dbt Models** (if not already done):
   ```bash
   cd medical_warehouse
   dbt run
   ```

### Run the Analysis

```bash
python scripts/run_notebook_analysis.py
```

## What It Shows

The script will display:

1. **Raw Data Overview** - Statistics and sample data from `raw.telegram_messages`
2. **Staging Layer** - Cleaned data statistics
3. **Dimension Tables** - Channels and dates
4. **Fact Table Analysis** - Message statistics and sample data
5. **Business Questions** - Answers to key questions:
   - Top 10 mentioned products
   - Price mentions across channels
   - Visual content analysis
   - Product type distribution
6. **Summary Statistics** - Complete data warehouse summary

## Troubleshooting

### "Connection refused"
- Start PostgreSQL: `docker-compose up -d`
- Check if running: `docker ps`

### "Relation does not exist"
- Load data: `python scripts/load_raw_to_postgres.py`
- Run dbt: `cd medical_warehouse && dbt run`

### "No data found"
- Make sure you've scraped data first (Task 1)
- Check if JSON files exist in `data/raw/telegram_messages/`

## Alternative: Use Jupyter Notebook

For interactive exploration with visualizations:

```bash
# Install Jupyter
pip install jupyter matplotlib seaborn

# Start Jupyter
jupyter notebook

# Open notebooks/explore_data_warehouse.ipynb
```
