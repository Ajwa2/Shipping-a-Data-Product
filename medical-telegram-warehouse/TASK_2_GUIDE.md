# Task 2 - Data Modeling and Transformation Guide

## Overview
This guide will help you complete Task 2: Transform raw, messy data into a clean, structured data warehouse using dbt and dimensional modeling.

## Prerequisites

1. **PostgreSQL Database Running**
   - Ensure PostgreSQL is running (via Docker or local installation)
   - Database should be accessible via `DATABASE_URL` in `.env`

2. **dbt Installed**
   ```bash
   pip install dbt-postgres
   ```

3. **Raw Data Available**
   - Complete Task 1 first to have JSON files in the data lake

## Step 1: Load Raw Data to PostgreSQL

### Option 1: Using the Script (Recommended)

```bash
python scripts/load_raw_to_postgres.py
```

This script will:
- Create `raw` schema in PostgreSQL
- Create `raw.telegram_messages` table
- Load all JSON files from the data lake
- Handle duplicates automatically

### Option 2: Manual Loading

```python
from src.loader.postgres_loader import PostgresLoader

loader = PostgresLoader()
loader.create_raw_table()
loader.load_from_directory(Path("data/raw/telegram_messages/2024-01-15"))
loader.close()
```

### Verify Data Loaded

```sql
-- Connect to PostgreSQL and run:
SELECT COUNT(*) FROM raw.telegram_messages;
SELECT channel_name, COUNT(*) 
FROM raw.telegram_messages 
GROUP BY channel_name;
```

## Step 2: Configure dbt

### Verify dbt Project Structure

The dbt project is already initialized at `medical_warehouse/`. Verify:

```bash
cd medical-telegram-warehouse
ls medical_warehouse/
```

Should show:
- `dbt_project.yml`
- `profiles.yml`
- `models/` directory
- `tests/` directory

### Update profiles.yml

Ensure `medical_warehouse/profiles.yml` has correct database connection:

```yaml
medical_warehouse:
  target: dev
  outputs:
    dev:
      type: postgres
      host: localhost
      user: postgres
      password: postgres
      port: 5432
      dbname: medical_warehouse
      schema: public
      threads: 4
```

### Install dbt Packages

```bash
cd medical_warehouse
dbt deps
```

This installs `dbt_utils` package for additional test macros.

## Step 3: Run dbt Models

### Test Connection

```bash
cd medical_warehouse
dbt debug
```

Should show "Connection test: [OK]"

### Run Staging Models

```bash
dbt run --models staging
```

This creates the `stg_messages` view with cleaned data.

### Run All Models

```bash
dbt run
```

This will:
1. Create `stg_messages` (staging view)
2. Create `dim_dates` (date dimension table)
3. Create `dim_channels` (channel dimension table)
4. Create `fct_messages` (fact table)

### Verify Models Created

```sql
-- Check staging model
SELECT COUNT(*) FROM stg_messages;

-- Check dimensions
SELECT COUNT(*) FROM dim_dates;
SELECT COUNT(*) FROM dim_channels;

-- Check fact table
SELECT COUNT(*) FROM fct_messages;
```

## Step 4: Run dbt Tests

### Run All Tests

```bash
dbt test
```

This runs:
- Built-in tests (unique, not_null, relationships)
- Custom tests in `tests/` directory

### Run Specific Tests

```bash
# Test staging models only
dbt test --models staging

# Test marts only
dbt test --models marts

# Run a specific test
dbt test --select assert_no_future_messages
```

### Expected Test Results

All tests should pass:
- ✅ `stg_messages.message_id` is unique and not null
- ✅ `dim_channels.channel_key` is unique and not null
- ✅ `dim_dates.date_key` is unique and not null
- ✅ `fct_messages` has valid foreign keys
- ✅ No future dates in messages
- ✅ No negative view/forward counts
- ✅ Valid date ranges

## Step 5: Generate Documentation

### Generate Docs

```bash
dbt docs generate
```

### Serve Documentation

```bash
dbt docs serve
```

This opens a web interface at `http://localhost:8080` showing:
- Model lineage graph
- Column descriptions
- Test results
- Source data documentation

## Star Schema Design

### Architecture

```
┌─────────────┐
│ dim_dates   │
│ - date_key  │
│ - full_date │
│ - day_name  │
│ - month     │
│ - quarter   │
│ - year      │
│ - is_weekend│
└─────────────┘
       ▲
       │
       │ FK
       │
┌─────────────┐      ┌──────────────┐
│fct_messages │──────│ dim_channels │
│ - message_id│      │ - channel_key│
│ - channel_key│◄────│ - channel_name│
│ - date_key  │      │ - channel_type│
│ - message_text│    │ - total_posts│
│ - view_count│      │ - avg_views  │
│ - forward_ct│      └──────────────┘
│ - has_image │
│ - product_type│
└─────────────┘
```

### Design Decisions

1. **Surrogate Keys**: Used integer surrogate keys (`channel_key`, `date_key`) instead of natural keys for:
   - Better join performance
   - Handling of changing natural keys
   - Standard dimensional modeling practice

2. **Date Dimension**: Pre-populated date dimension from 2020 to future year:
   - Enables time-based analysis without gaps
   - Includes business-friendly attributes (day names, quarters, weekends)
   - Supports filtering and grouping by time periods

3. **Channel Classification**: Automatic classification based on channel name:
   - Pharmaceutical: channels with "pharma", "drug", "medicine"
   - Cosmetics: channels with "cosmetic", "beauty", "skincare"
   - Medical: channels with "medical", "health", "clinic"
   - Other: default category

4. **Fact Table Design**:
   - One row per message (grain)
   - Foreign keys to dimensions only (no denormalized attributes)
   - Business logic fields (product_type, mentions_price) for analytics
   - Engagement metrics (views, forwards) as measures

5. **Staging Layer**:
   - Cleans and validates raw data
   - Handles nulls and invalid values
   - Adds calculated fields
   - Filters invalid records

## Custom Tests Explained

### assert_no_future_messages.sql
Ensures data quality by preventing messages with future dates from entering the warehouse.

### assert_positive_views.sql
Business rule: View counts cannot be negative.

### assert_positive_forwards.sql
Business rule: Forward counts cannot be negative.

### assert_valid_message_dates.sql
Ensures message dates are within reasonable range (2020 onwards, not more than 1 day in future).

### assert_no_orphaned_fact_records.sql
Referential integrity: All fact records must have valid foreign keys to dimensions.

## Troubleshooting

### "Schema 'raw' does not exist"
Run the loader script first to create the raw schema:
```bash
python scripts/load_raw_to_postgres.py
```

### "Relation does not exist"
Ensure you've run `dbt run` to create the models:
```bash
dbt run
```

### "Connection test failed"
Check your `profiles.yml` and ensure PostgreSQL is running:
```bash
dbt debug
```

### Tests Failing
- Review test output to identify failing rows
- Check data quality in raw table
- Adjust staging model filters if needed

## Deliverables Checklist

- [x] Script to load raw data to PostgreSQL (`scripts/load_raw_to_postgres.py`)
- [x] Raw schema and table created (`raw.telegram_messages`)
- [x] Staging model with data cleaning (`stg_messages.sql`)
- [x] Date dimension table (`dim_dates.sql`)
- [x] Channel dimension table (`dim_channels.sql`)
- [x] Messages fact table (`fct_messages.sql`)
- [x] dbt tests in schema.yml (unique, not_null, relationships)
- [x] Custom data tests (5 tests in `tests/` directory)
- [x] Documentation in schema.yml files
- [x] Generated dbt documentation

## Next Steps

After completing Task 2, proceed to:
- **Task 3**: Data Enrichment with YOLO
- **Task 4**: Build Analytical API
- **Task 5**: Orchestration with Dagster
