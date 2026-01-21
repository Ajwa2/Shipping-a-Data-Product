"""
FastAPI main application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from api.database import engine, Base
from api import schemas
from api import analytics

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Medical Telegram Warehouse API",
    description="""
    Analytical API for medical data warehouse from Telegram sources.
    
    ## Features
    
    * **Top Products**: Find most frequently mentioned products/terms
    * **Channel Activity**: Get detailed statistics for specific channels
    * **Message Search**: Search messages by keyword
    * **Visual Content Stats**: Analyze image usage and YOLO detection results
    
    ## Data Sources
    
    All endpoints query the transformed data warehouse built with dbt:
    - `fct_messages`: Fact table with message data
    - `dim_channels`: Channel dimension
    - `fct_image_detections`: Image analysis results from YOLO
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analytics.router)

@app.get("/", tags=["general"])
async def root():
    """
    Root endpoint - API information and available endpoints
    """
    return {
        "message": "Medical Telegram Warehouse API",
        "version": "1.0.0",
        "description": "Analytical API for medical Telegram data warehouse",
        "endpoints": {
            "top_products": "/api/reports/top-products?limit=10",
            "channel_activity": "/api/channels/{channel_name}/activity",
            "search_messages": "/api/search/messages?query=keyword&limit=20",
            "visual_content": "/api/reports/visual-content",
            "docs": "/docs",
            "health": "/health"
        },
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc"
        }
    }

@app.get("/health", tags=["general"])
async def health_check():
    """
    Health check endpoint
    
    Returns API and database connection status
    """
    from api.database import engine
    try:
        # Test database connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "api_version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }
