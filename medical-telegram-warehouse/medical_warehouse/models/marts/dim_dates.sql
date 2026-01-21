{{ config(materialized='table') }}

WITH date_spine AS (
    SELECT 
        generate_series(
            '2020-01-01'::date,
            CURRENT_DATE + INTERVAL '1 year',
            '1 day'::interval
        )::date AS full_date
)

SELECT
    -- Surrogate key (YYYYMMDD format)
    TO_CHAR(full_date, 'YYYYMMDD')::INTEGER as date_key,
    
    -- Full date
    full_date,
    
    -- Day information
    EXTRACT(DAY FROM full_date) as day_of_month,
    EXTRACT(DOW FROM full_date) as day_of_week,  -- 0=Sunday, 6=Saturday
    TO_CHAR(full_date, 'Day') as day_name,
    TO_CHAR(full_date, 'Dy') as day_name_short,
    
    -- Week information
    EXTRACT(WEEK FROM full_date) as week_of_year,
    TO_CHAR(full_date, 'WW')::INTEGER as iso_week_number,
    DATE_TRUNC('week', full_date)::date as week_start_date,
    
    -- Month information
    EXTRACT(MONTH FROM full_date) as month,
    TO_CHAR(full_date, 'Month') as month_name,
    TO_CHAR(full_date, 'Mon') as month_name_short,
    DATE_TRUNC('month', full_date)::date as month_start_date,
    
    -- Quarter information
    EXTRACT(QUARTER FROM full_date) as quarter,
    CASE 
        WHEN EXTRACT(QUARTER FROM full_date) = 1 THEN 'Q1'
        WHEN EXTRACT(QUARTER FROM full_date) = 2 THEN 'Q2'
        WHEN EXTRACT(QUARTER FROM full_date) = 3 THEN 'Q3'
        ELSE 'Q4'
    END as quarter_name,
    DATE_TRUNC('quarter', full_date)::date as quarter_start_date,
    
    -- Year information
    EXTRACT(YEAR FROM full_date) as year,
    DATE_TRUNC('year', full_date)::date as year_start_date,
    
    -- Flags
    CASE 
        WHEN EXTRACT(DOW FROM full_date) IN (0, 6) THEN TRUE
        ELSE FALSE
    END as is_weekend,
    CASE 
        WHEN EXTRACT(DOW FROM full_date) BETWEEN 1 AND 5 THEN TRUE
        ELSE FALSE
    END as is_weekday,
    
    -- Fiscal year (assuming Ethiopian calendar - adjust as needed)
    -- For simplicity, using Gregorian calendar
    EXTRACT(YEAR FROM full_date) as fiscal_year

FROM date_spine
ORDER BY full_date
