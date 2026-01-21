# Medical Telegram Warehouse

An end-to-end data pipeline for Telegram medical channels, leveraging dbt for transformation, Dagster for orchestration, and YOLOv8 for data enrichment.

## Overview

This project builds a robust data platform that generates actionable insights about Ethiopian medical businesses using data scraped from public Telegram channels. The pipeline implements a modern ELT (Extract, Load, Transform) framework with:

- **Data Lake**: Raw data storage (JSON + images)
- **PostgreSQL**: Data warehouse
- **dbt**: Data transformations and star schema modeling
- **Dagster**: Pipeline orchestration
- **YOLOv8**: Image object detection for enrichment
- **FastAPI**: Analytical API for insights

## Project Structure

```
medical-telegram-warehouse/
├── .vscode/                    # VS Code settings
├── .github/                    # GitHub workflows
├── .env                        # Environment variables (DO NOT COMMIT)
├── docker-compose.yml          # Container orchestration
├── Dockerfile                  # Python environment
├── requirements.txt            # Python dependencies
├── dagster.yaml                # Dagster configuration
├── data/                       # Raw and processed data
│   ├── raw/
│   │   ├── telegram_messages/  # Partitioned JSON files
│   │   ├── images/             # Downloaded images
│   │   └── csv/                # CSV backups
├── medical_warehouse/          # dbt project
│   ├── models/
│   │   ├── staging/            # Staging models
│   │   └── marts/              # Star schema (dim/fct tables)
│   └── profiles.yml            # dbt database profiles
├── src/                        # Source code
│   ├── scraper/                # Telegram scraper
│   ├── loader/                 # PostgreSQL loader
│   ├── enrichment/             # YOLO enricher
│   └── orchestration/          # Dagster pipeline
├── api/                        # FastAPI application
│   ├── main.py                 # FastAPI app
│   ├── database.py             # Database connection
│   ├── schemas.py              # Pydantic models
│   └── analytics.py            # Analytical endpoints
├── notebooks/                  # Jupyter notebooks
├── tests/                      # Unit tests
└── scripts/                    # Utility scripts
    ├── scrape_telegram.py      # Standalone scraper
    ├── load_to_postgres.py     # Standalone loader
    ├── enrich_with_yolo.py     # Standalone enricher
    └── run_pipeline.py         # Pipeline runner
```

## Setup

### 1. Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL 15+ (or use Docker)
- Telegram API credentials (from https://my.telegram.org/apps)

### 2. Environment Setup

Create a `.env` file in the project root:

```bash
# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=medical_warehouse
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/medical_warehouse

# Telegram API
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_PHONE=your_phone_number_here

# API Configuration
API_SECRET_KEY=your_secret_key_here
API_DEBUG=True
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start Services

```bash
docker-compose up -d
```

This starts:
- PostgreSQL on `localhost:5432`
- FastAPI on `http://localhost:8000`

### 5. Initialize Database Tables

The tables will be created automatically when you run the loader or start the API.

## Usage

### Option 1: Run Individual Scripts

#### Scrape Telegram Channels

```bash
python scripts/scrape_telegram.py @cheMed123 @lobelia4cosmetics @tikvahpharma
```

#### Load Data to PostgreSQL

```bash
python scripts/load_to_postgres.py
```

#### Enrich with YOLO

```bash
python scripts/enrich_with_yolo.py 100  # Process 100 images
```

### Option 2: Use Dagster Pipeline

#### Start Dagster UI

```bash
dagster dev -m src.orchestration.pipeline
```

Then access the Dagster UI at `http://localhost:3000`

#### Run Pipeline Manually

```bash
dagster asset materialize -m src.orchestration.pipeline scrape_telegram_channels load_to_postgres enrich_with_yolo run_dbt_models
```

### Option 3: Run dbt Models

```bash
cd medical_warehouse
dbt run
dbt test
```

## API Endpoints

Once the API is running, access the interactive docs at `http://localhost:8000/docs`

### Available Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `GET /analytics/top-products` - Top mentioned products
- `GET /analytics/channel-stats` - Statistics per channel
- `GET /analytics/product-price-analysis` - Price analysis
- `GET /analytics/visual-content-analysis` - YOLO detection analysis
- `GET /analytics/posting-trends` - Daily/weekly posting trends
- `GET /analytics/product-types` - Product type distribution

## Data Pipeline Flow

```
1. Telegram Channels
   ↓
2. Telegram Scraper → Data Lake (JSON + Images)
   ↓
3. PostgreSQL Loader → raw_messages table
   ↓
4. YOLO Enricher → enriched_messages table
   ↓
5. dbt Transformations → Star Schema (dim_channels, fct_messages, etc.)
   ↓
6. FastAPI Analytics → Insights & Reports
```

## Business Questions Answered

1. **Top Products**: `/analytics/top-products` - Most frequently mentioned products
2. **Price Analysis**: `/analytics/product-price-analysis` - Price mentions across channels
3. **Visual Content**: `/analytics/visual-content-analysis` - YOLO detections (pills vs creams)
4. **Posting Trends**: `/analytics/posting-trends` - Daily/weekly volume trends
5. **Channel Stats**: `/analytics/channel-stats` - Media ratio, views, forwards per channel

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Adding New Channels

Edit `src/orchestration/pipeline.py` or pass channels as arguments to the scraper script.

### Customizing YOLO Model

Update the model path in `src/enrichment/yolo_enricher.py`:

```python
enricher = YOLOEnricher(model_path="path/to/custom_model.pt")
```

## Troubleshooting

### Telegram Authentication

On first run, you'll need to authenticate with Telegram. The scraper will prompt for a phone number and verification code.

### Database Connection

Ensure PostgreSQL is running and `DATABASE_URL` in `.env` is correct.

### YOLO Model Download

The YOLOv8 model will be downloaded automatically on first use (~6MB).

## License

MIT
