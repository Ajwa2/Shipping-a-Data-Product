"""
Run notebook analysis and display output
This script executes the notebook code sequentially and shows results
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 70)
print("MEDICAL TELEGRAM WAREHOUSE - DATA EXPLORATION")
print("=" * 70)
print()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/medical_warehouse")
print("Connecting to database...")
try:
    engine = create_engine(DATABASE_URL)
    # Test connection
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("[OK] Database connection established")
    print()
except Exception as e:
    print(f"[ERROR] Database connection failed: {e}")
    print()
    print("Please check:")
    print("  1. PostgreSQL is running (start with: docker-compose up -d)")
    print("  2. DATABASE_URL in .env is correct")
    print("  3. Database 'medical_warehouse' exists")
    print()
    print("To start PostgreSQL:")
    print("  cd medical-telegram-warehouse")
    print("  docker-compose up -d")
    sys.exit(1)

# ============================================================================
# 1. Raw Data Overview
# ============================================================================
print("=" * 70)
print("1. RAW DATA OVERVIEW")
print("=" * 70)
print()

try:
    raw_query = """
    SELECT 
        COUNT(*) as total_messages,
        COUNT(DISTINCT channel_name) as unique_channels,
        MIN(message_date) as earliest_message,
        MAX(message_date) as latest_message,
        COUNT(CASE WHEN has_media THEN 1 END) as messages_with_media
    FROM raw.telegram_messages
    """
    
    raw_stats = pd.read_sql(raw_query, engine)
    print("Raw Data Statistics:")
    print("-" * 70)
    print(raw_stats.to_string(index=False))
    print()
    
    # Show sample raw data
    raw_sample = pd.read_sql("SELECT * FROM raw.telegram_messages LIMIT 5", engine)
    print("Sample Raw Data (first 5 rows):")
    print("-" * 70)
    print(raw_sample.to_string(index=False))
    print()
    
except Exception as e:
    print(f"[ERROR] Error reading raw data: {e}")
    print("Make sure you've run: python scripts/load_raw_to_postgres.py")
    print()

# ============================================================================
# 2. Staging Layer (Cleaned Data)
# ============================================================================
print("=" * 70)
print("2. STAGING LAYER (CLEANED DATA)")
print("=" * 70)
print()

try:
    staging_query = """
    SELECT 
        COUNT(*) as total_messages,
        COUNT(DISTINCT channel_name) as unique_channels,
        ROUND(AVG(message_length), 2) as avg_message_length,
        COUNT(CASE WHEN has_image THEN 1 END) as messages_with_images,
        ROUND(AVG(views), 2) as avg_views,
        ROUND(AVG(forwards), 2) as avg_forwards
    FROM stg_messages
    """
    
    staging_stats = pd.read_sql(staging_query, engine)
    print("Staging Layer Statistics:")
    print("-" * 70)
    print(staging_stats.to_string(index=False))
    print()
    
    # Show sample staging data
    staging_sample = pd.read_sql("SELECT * FROM stg_messages LIMIT 5", engine)
    print("Sample Staging Data (first 5 rows):")
    print("-" * 70)
    # Show only key columns for readability
    key_cols = ['message_id', 'channel_name', 'message_date', 'message_length', 'has_image', 'views']
    available_cols = [col for col in key_cols if col in staging_sample.columns]
    print(staging_sample[available_cols].to_string(index=False))
    print()
    
except Exception as e:
    print(f"[ERROR] Error reading staging data: {e}")
    print("Make sure you've run: cd medical_warehouse && dbt run")
    print()

# ============================================================================
# 3. Dimension Tables
# ============================================================================
print("=" * 70)
print("3. DIMENSION TABLES")
print("=" * 70)
print()

try:
    # Channel Dimension
    channels = pd.read_sql("SELECT * FROM dim_channels ORDER BY total_posts DESC", engine)
    print("Channel Dimension:")
    print("-" * 70)
    print(channels.to_string(index=False))
    print()
    
    # Date Dimension Sample
    dates_sample = pd.read_sql("""
        SELECT * FROM dim_dates 
        WHERE full_date >= CURRENT_DATE - INTERVAL '7 days'
        ORDER BY full_date DESC
        LIMIT 10
    """, engine)
    print("Recent Date Dimension Sample (last 7 days):")
    print("-" * 70)
    key_date_cols = ['date_key', 'full_date', 'day_name', 'month_name', 'year', 'is_weekend']
    available_date_cols = [col for col in key_date_cols if col in dates_sample.columns]
    print(dates_sample[available_date_cols].to_string(index=False))
    print()
    
except Exception as e:
    print(f"[ERROR] Error reading dimension tables: {e}")
    print("Make sure you've run: cd medical_warehouse && dbt run")
    print()

# ============================================================================
# 4. Fact Table Analysis
# ============================================================================
print("=" * 70)
print("4. FACT TABLE ANALYSIS")
print("=" * 70)
print()

try:
    fact_stats = pd.read_sql("""
    SELECT 
        COUNT(*) as total_messages,
        SUM(view_count) as total_views,
        SUM(forward_count) as total_forwards,
        ROUND(AVG(view_count), 2) as avg_views,
        ROUND(AVG(forward_count), 2) as avg_forwards,
        COUNT(CASE WHEN has_image THEN 1 END) as messages_with_images,
        COUNT(CASE WHEN mentions_price THEN 1 END) as messages_mentioning_price
    FROM fct_messages
    """, engine)
    
    print("Fact Table Statistics:")
    print("-" * 70)
    print(fact_stats.to_string(index=False))
    print()
    
    # Sample fact data
    fact_sample = pd.read_sql("""
        SELECT 
            fm.message_id,
            dc.channel_name,
            dd.full_date,
            LEFT(fm.message_text, 50) as message_preview,
            fm.view_count,
            fm.product_type,
            fm.mentions_price
        FROM fct_messages fm
        JOIN dim_channels dc ON fm.channel_key = dc.channel_key
        JOIN dim_dates dd ON fm.date_key = dd.date_key
        LIMIT 10
    """, engine)
    
    print("Sample Fact Table Data (with dimensions, first 10 rows):")
    print("-" * 70)
    print(fact_sample.to_string(index=False))
    print()
    
except Exception as e:
    print(f"[ERROR] Error reading fact table: {e}")
    print("Make sure you've run: cd medical_warehouse && dbt run")
    print()

# ============================================================================
# 5. Business Questions Analysis
# ============================================================================
print("=" * 70)
print("5. BUSINESS QUESTIONS ANALYSIS")
print("=" * 70)
print()

# Q1: Top 10 Most Frequently Mentioned Products
print("-" * 70)
print("Q1: Top 10 Most Frequently Mentioned Products/Drugs")
print("-" * 70)
try:
    top_products = pd.read_sql("""
        SELECT 
            LEFT(message_text, 100) as message_text,
            COUNT(*) as mention_count,
            ROUND(AVG(view_count), 2) as avg_views
        FROM fct_messages
        WHERE message_text IS NOT NULL
            AND LENGTH(message_text) > 10
        GROUP BY message_text
        ORDER BY mention_count DESC
        LIMIT 10
    """, engine)
    print(top_products.to_string(index=False))
    print()
except Exception as e:
    print(f"Error: {e}")
    print()

# Q2: Price Mentions Across Channels
print("-" * 70)
print("Q2: Price Mentions Across Channels")
print("-" * 70)
try:
    price_analysis = pd.read_sql("""
        SELECT 
            dc.channel_name,
            dc.channel_type,
            COUNT(*) as total_messages,
            COUNT(CASE WHEN fm.mentions_price THEN 1 END) as price_mentions,
            ROUND(COUNT(CASE WHEN fm.mentions_price THEN 1 END)::NUMERIC / 
                  NULLIF(COUNT(*), 0) * 100, 2) as price_mention_percentage
        FROM fct_messages fm
        JOIN dim_channels dc ON fm.channel_key = dc.channel_key
        GROUP BY dc.channel_name, dc.channel_type
        ORDER BY price_mention_percentage DESC
    """, engine)
    print(price_analysis.to_string(index=False))
    print()
except Exception as e:
    print(f"Error: {e}")
    print()

# Q3: Visual Content Analysis
print("-" * 70)
print("Q3: Visual Content Analysis (Channels with Most Images)")
print("-" * 70)
try:
    visual_content = pd.read_sql("""
        SELECT 
            dc.channel_name,
            dc.channel_type,
            COUNT(*) as total_messages,
            COUNT(CASE WHEN fm.has_image THEN 1 END) as messages_with_images,
            ROUND(COUNT(CASE WHEN fm.has_image THEN 1 END)::NUMERIC / 
                  NULLIF(COUNT(*), 0) * 100, 2) as image_percentage
        FROM fct_messages fm
        JOIN dim_channels dc ON fm.channel_key = dc.channel_key
        GROUP BY dc.channel_name, dc.channel_type
        ORDER BY image_percentage DESC
    """, engine)
    print(visual_content.to_string(index=False))
    print()
except Exception as e:
    print(f"Error: {e}")
    print()

# Q4: Product Type Distribution
print("-" * 70)
print("Q4: Product Type Distribution")
print("-" * 70)
try:
    product_types = pd.read_sql("""
        SELECT 
            product_type,
            COUNT(*) as message_count,
            ROUND(AVG(view_count), 2) as avg_views,
            ROUND(AVG(forward_count), 2) as avg_forwards
        FROM fct_messages
        WHERE product_type IS NOT NULL
        GROUP BY product_type
        ORDER BY message_count DESC
    """, engine)
    print(product_types.to_string(index=False))
    print()
except Exception as e:
    print(f"Error: {e}")
    print()

# ============================================================================
# 6. Summary Statistics
# ============================================================================
print("=" * 70)
print("6. SUMMARY STATISTICS")
print("=" * 70)
print()

try:
    summary = pd.read_sql("""
        SELECT 
            'Total Messages' as metric,
            COUNT(*)::text as value
        FROM fct_messages
        
        UNION ALL
        
        SELECT 
            'Total Channels' as metric,
            COUNT(*)::text as value
        FROM dim_channels
        
        UNION ALL
        
        SELECT 
            'Total Views' as metric,
            SUM(view_count)::text as value
        FROM fct_messages
        
        UNION ALL
        
        SELECT 
            'Total Forwards' as metric,
            SUM(forward_count)::text as value
        FROM fct_messages
        
        UNION ALL
        
        SELECT 
            'Messages with Images' as metric,
            COUNT(CASE WHEN has_image THEN 1 END)::text as value
        FROM fct_messages
        
        UNION ALL
        
        SELECT 
            'Messages Mentioning Price' as metric,
            COUNT(CASE WHEN mentions_price THEN 1 END)::text as value
        FROM fct_messages
    """, engine)
    
    print(summary.to_string(index=False))
    print()
    
except Exception as e:
    print(f"Error: {e}")
    print()

print("=" * 70)
print("[SUCCESS] DATA EXPLORATION COMPLETE!")
print("=" * 70)
print()
print("Note: For visualizations, please use the Jupyter notebook:")
print("  jupyter notebook notebooks/explore_data_warehouse.ipynb")
