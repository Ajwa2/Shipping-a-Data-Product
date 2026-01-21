"""
Script to run the FastAPI server
Task 4 - Analytical API
"""
import uvicorn
import os
from pathlib import Path

if __name__ == "__main__":
    # Get project root
    project_root = Path(__file__).parent.parent
    
    print("=" * 70)
    print("Medical Telegram Warehouse API")
    print("=" * 70)
    print()
    print("Starting FastAPI server...")
    print()
    print("API Documentation:")
    print("  - Swagger UI: http://localhost:8000/docs")
    print("  - ReDoc: http://localhost:8000/redoc")
    print()
    print("Available Endpoints:")
    print("  - GET /api/reports/top-products?limit=10")
    print("  - GET /api/channels/{channel_name}/activity")
    print("  - GET /api/search/messages?query=keyword&limit=20")
    print("  - GET /api/reports/visual-content")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 70)
    print()
    
    # Run the server
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
