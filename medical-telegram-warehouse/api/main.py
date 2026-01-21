"""
FastAPI main application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.database import engine, Base
from api import schemas
from api import analytics

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Medical Telegram Warehouse API",
    description="API for medical data warehouse from Telegram sources",
    version="1.0.0"
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

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Medical Telegram Warehouse API",
        "version": "1.0.0",
        "endpoints": {
            "analytics": "/analytics",
            "docs": "/docs",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
