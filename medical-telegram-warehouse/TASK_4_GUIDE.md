# Task 4 - Build an Analytical API

## Overview

This task implements a REST API using FastAPI to expose the data warehouse through analytical endpoints. The API provides business intelligence queries on the transformed data.

## Implementation

### API Endpoints

1. **GET `/api/reports/top-products?limit=10`**
   - Returns most frequently mentioned terms/products across all channels
   - Includes mention counts, average views, and channels where terms appear
   - Query parameter: `limit` (1-100, default: 10)

2. **GET `/api/channels/{channel_name}/activity`**
   - Returns posting activity and trends for a specific channel
   - Includes statistics: total posts, media ratio, engagement metrics, date ranges
   - Path parameter: `channel_name` (e.g., 'chemed123')
   - Returns recent posts summary

3. **GET `/api/search/messages?query=keyword&limit=20`**
   - Searches for messages containing a specific keyword
   - Returns matching messages with full details including engagement metrics
   - Query parameters:
     - `query`: Search keyword (required, min 2 characters)
     - `limit`: Maximum results (1-100, default: 20)

4. **GET `/api/reports/visual-content`**
   - Returns comprehensive statistics about image usage across channels
   - Includes YOLO detection results, image categories, engagement metrics
   - Returns top detected objects and channel-level statistics

### Additional Endpoints

- **GET `/`** - API information and endpoint list
- **GET `/health`** - Health check with database connection status
- **GET `/docs`** - Swagger UI documentation (auto-generated)
- **GET `/redoc`** - ReDoc documentation (auto-generated)

## Running the API

### Option 1: Using the script
```bash
cd medical-telegram-warehouse
python scripts/run_api.py
```

### Option 2: Using uvicorn directly
```bash
cd medical-telegram-warehouse
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 3: Using Docker (if configured)
```bash
docker-compose up api
```

## Accessing the API

Once running, access:
- **API Base URL**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Example Requests

### 1. Get Top Products
```bash
curl "http://localhost:8000/api/reports/top-products?limit=10"
```

### 2. Get Channel Activity
```bash
curl "http://localhost:8000/api/channels/chemed123/activity"
```

### 3. Search Messages
```bash
curl "http://localhost:8000/api/search/messages?query=paracetamol&limit=20"
```

### 4. Get Visual Content Stats
```bash
curl "http://localhost:8000/api/reports/visual-content"
```

## Data Validation

All endpoints use Pydantic models for:
- **Request validation**: Query parameters and path parameters
- **Response validation**: Structured response schemas
- **Error handling**: Proper HTTP status codes and error messages

## Error Handling

The API includes:
- **404 Not Found**: Channel not found, resource doesn't exist
- **400 Bad Request**: Invalid parameters (e.g., limit out of range)
- **500 Internal Server Error**: Database or processing errors
- **Error responses**: Structured error messages with details

## API Documentation

FastAPI automatically generates OpenAPI/Swagger documentation:
- Access at `/docs` for interactive Swagger UI
- Access at `/redoc` for ReDoc documentation
- All endpoints include descriptions and parameter documentation
- Response schemas are documented with examples

## Testing the API

### Using curl
```bash
# Health check
curl http://localhost:8000/health

# Top products
curl "http://localhost:8000/api/reports/top-products?limit=5"

# Channel activity
curl http://localhost:8000/api/channels/chemed123/activity

# Search messages
curl "http://localhost:8000/api/search/messages?query=medicine&limit=10"

# Visual content stats
curl http://localhost:8000/api/reports/visual-content
```

### Using Python requests
```python
import requests

# Top products
response = requests.get("http://localhost:8000/api/reports/top-products?limit=10")
print(response.json())

# Channel activity
response = requests.get("http://localhost:8000/api/channels/chemed123/activity")
print(response.json())
```

### Using Swagger UI
1. Navigate to http://localhost:8000/docs
2. Click on any endpoint
3. Click "Try it out"
4. Enter parameters
5. Click "Execute"
6. View response

## Files Created

- `api/analytics.py` - Analytical endpoint implementations
- `api/schemas.py` - Pydantic models for request/response validation
- `api/main.py` - FastAPI application with enhanced documentation
- `scripts/run_api.py` - Script to run the API server

## Next Steps

1. **Test all endpoints** using Swagger UI or curl
2. **Take screenshots** of:
   - Swagger UI documentation page
   - Example API responses
   - ReDoc documentation
3. **Document findings** in your report
4. **Consider enhancements**:
   - Add authentication/authorization
   - Add rate limiting
   - Add caching for frequently accessed data
   - Add pagination for large result sets
