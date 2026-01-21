# Jupyter Notebooks

This directory contains Jupyter notebooks for exploring and analyzing the data warehouse.

## Setup

1. **Install Jupyter and dependencies**:
   ```bash
   pip install jupyter ipykernel matplotlib seaborn
   ```

2. **Start Jupyter**:
   ```bash
   jupyter notebook
   ```
   
   Or use JupyterLab:
   ```bash
   jupyter lab
   ```

3. **Open the notebook**:
   - Navigate to `notebooks/explore_data_warehouse.ipynb`
   - Make sure your `.env` file has the correct `DATABASE_URL`

## Notebooks

### explore_data_warehouse.ipynb

Comprehensive exploration notebook that includes:

1. **Raw Data Overview**
   - Statistics from `raw.telegram_messages`
   - Sample data preview

2. **Staging Layer Analysis**
   - Cleaned data statistics
   - Data quality metrics

3. **Dimension Tables**
   - Channel dimension exploration
   - Date dimension sample

4. **Fact Table Analysis**
   - Message statistics
   - Engagement metrics

5. **Visualizations**
   - Messages by channel
   - Channel type distribution
   - Daily posting trends
   - Product type analysis
   - Engagement metrics

6. **Business Questions**
   - Top 10 mentioned products
   - Price mentions across channels
   - Visual content analysis
   - Posting trends by day of week

7. **Summary Statistics**
   - Complete data warehouse summary

## Prerequisites

- PostgreSQL database running with data loaded
- dbt models run (`dbt run`)
- Environment variables configured in `.env`

## Usage Tips

1. **Run cells sequentially** - Some cells depend on previous ones
2. **Check database connection** - First cell tests the connection
3. **Adjust date ranges** - Modify SQL queries to explore different time periods
4. **Customize visualizations** - Modify matplotlib/seaborn code for your needs

## Troubleshooting

### "No module named 'X'"
Install missing packages:
```bash
pip install -r requirements.txt
```

### "Connection refused"
- Check PostgreSQL is running
- Verify `DATABASE_URL` in `.env`
- Test connection: `psql $DATABASE_URL`

### "Relation does not exist"
Run dbt models first:
```bash
cd medical_warehouse
dbt run
```
