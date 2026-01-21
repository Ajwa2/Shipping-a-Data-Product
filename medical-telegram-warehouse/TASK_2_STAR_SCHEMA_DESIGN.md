# Star Schema Design Decisions

## Overview

This document explains the dimensional modeling decisions for the medical telegram warehouse data model.

## Schema Structure

### Fact Table: `fct_messages`

**Grain**: One row per message

**Measures**:
- `view_count`: Number of views (additive)
- `forward_count`: Number of forwards (additive)
- `message_length`: Length of message text (non-additive, for analysis)

**Foreign Keys**:
- `channel_key` → `dim_channels.channel_key`
- `date_key` → `dim_dates.date_key`

**Business Logic Fields**:
- `product_type`: Inferred product category (pill, cream, liquid, etc.)
- `mentions_price`: Boolean flag for price mentions
- `has_image`: Boolean flag for image presence

**Design Rationale**:
- Single fact table for all message events
- Foreign keys only (no denormalized attributes)
- Business logic fields pre-calculated for performance
- Includes both measures and descriptive attributes

### Dimension Table: `dim_channels`

**Surrogate Key**: `channel_key` (auto-incrementing integer)

**Natural Key**: `channel_name` (normalized channel identifier)

**Attributes**:
- `channel_title`: Display name
- `channel_type`: Classification (Pharmaceutical, Cosmetics, Medical, Other)
- `total_posts`: Aggregated count
- `avg_views`, `avg_forwards`: Aggregated metrics
- `first_post_date`, `last_post_date`: Date range
- `days_active`: Calculated duration

**Design Rationale**:
- Surrogate key for better join performance
- Type classification enables filtering by business category
- Aggregated metrics reduce need for joins in common queries
- Date range supports time-based channel analysis

**Type Classification Logic**:
- **Pharmaceutical**: Contains "pharma", "drug", "medicine"
- **Cosmetics**: Contains "cosmetic", "beauty", "skincare"
- **Medical**: Contains "medical", "health", "clinic"
- **Other**: Default category

### Dimension Table: `dim_dates`

**Surrogate Key**: `date_key` (YYYYMMDD format, e.g., 20240115)

**Attributes**:
- `full_date`: Actual date value
- `day_of_week`, `day_name`: Day information
- `month`, `month_name`: Month information
- `quarter`, `quarter_name`: Quarter information
- `year`: Year
- `is_weekend`, `is_weekday`: Boolean flags
- `week_of_year`: Week number

**Design Rationale**:
- Pre-populated date dimension eliminates gaps
- Business-friendly attributes (day names, quarters)
- Supports time-based analysis and filtering
- Weekend flags enable business day analysis

**Date Range**: 2020-01-01 to one year in the future
- Covers historical data needs
- Allows for future planning

## Data Flow

```
Raw Data (raw.telegram_messages)
    ↓
Staging Layer (stg_messages)
    - Data cleaning
    - Type casting
    - Validation
    - Calculated fields
    ↓
Dimension Tables
    - dim_dates (pre-populated)
    - dim_channels (aggregated from staging)
    ↓
Fact Table (fct_messages)
    - Joins to dimensions
    - Business logic fields
    - Measures
```

## Design Principles Applied

### 1. Star Schema Pattern
- Single fact table with multiple dimension tables
- Denormalized dimensions for query performance
- Clear separation of facts and dimensions

### 2. Surrogate Keys
- Integer surrogate keys for better performance
- Natural keys preserved as attributes
- Enables handling of changing dimensions

### 3. Pre-aggregation
- Channel statistics pre-calculated in `dim_channels`
- Reduces need for expensive aggregations
- Balances storage vs. query performance

### 4. Business Logic in Fact Table
- Product type inference in fact table
- Price mention detection in fact table
- Enables filtering without complex joins

### 5. Staging Layer
- Cleans raw data before transformation
- Validates data quality
- Adds calculated fields
- Filters invalid records

## Query Patterns Supported

### 1. Time-Based Analysis
```sql
SELECT 
    dd.month_name,
    COUNT(*) as message_count
FROM fct_messages fm
JOIN dim_dates dd ON fm.date_key = dd.date_key
GROUP BY dd.month_name
```

### 2. Channel Performance
```sql
SELECT 
    dc.channel_name,
    dc.channel_type,
    SUM(fm.view_count) as total_views
FROM fct_messages fm
JOIN dim_channels dc ON fm.channel_key = dc.channel_key
GROUP BY dc.channel_name, dc.channel_type
```

### 3. Product Type Distribution
```sql
SELECT 
    product_type,
    COUNT(*) as count
FROM fct_messages
GROUP BY product_type
```

### 4. Weekend vs Weekday Analysis
```sql
SELECT 
    dd.is_weekend,
    AVG(fm.view_count) as avg_views
FROM fct_messages fm
JOIN dim_dates dd ON fm.date_key = dd.date_key
GROUP BY dd.is_weekend
```

## Performance Considerations

1. **Indexes**: Consider adding indexes on:
   - `fct_messages.channel_key`
   - `fct_messages.date_key`
   - `dim_channels.channel_name` (for lookups)

2. **Materialization**:
   - Staging: View (lightweight, always fresh)
   - Dimensions: Table (pre-aggregated, faster queries)
   - Fact: Table (large dataset, better performance)

3. **Partitioning**: For large fact tables, consider partitioning by `date_key`

## Future Enhancements

1. **Slowly Changing Dimensions (SCD)**: If channel attributes change over time
2. **Additional Dimensions**: 
   - `dim_products` (if product catalog is available)
   - `dim_locations` (if geographic data is available)
3. **Fact Table Granularity**: Could add fact tables for:
   - Daily aggregations (`fct_daily_channel_stats`)
   - Product mentions (`fct_product_mentions`)

## Testing Strategy

1. **Referential Integrity**: All foreign keys must reference valid dimension keys
2. **Data Quality**: No negative values, no future dates
3. **Completeness**: All messages should have valid dimensions
4. **Business Rules**: Product types match expected values

This design provides a solid foundation for analytical queries while maintaining data quality and performance.
