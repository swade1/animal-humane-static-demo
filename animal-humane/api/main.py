"""
Refactored FastAPI application with improved structure
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any
import traceback
import asyncio
from functools import wraps

from fastapi import FastAPI, HTTPException, Depends, status, Request, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import config
from models.api_models import (
    DogResponse, DogUpdate, OverviewStats, 
    AdoptionRecord, OriginData, APIResponse
)
from services.dog_service import DogService
from services.elasticsearch_service import ElasticsearchService
from utils.logger import setup_logger

import os
import re
from pathlib import Path

# Setup logging
logger = setup_logger("api")

# Cache configuration
CACHE_DURATION = timedelta(minutes=30)  # Reduced to 30 minutes for fresher data
cache = {}

def cached(cache_key: str):
    """Decorator to cache async function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            now = datetime.now()
            
            # Check if we have cached data and it's still valid
            if cache_key in cache:
                cached_time, cached_data = cache[cache_key]
                if now - cached_time < CACHE_DURATION:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached_data
                else:
                    logger.debug(f"Cache expired for {cache_key}")
            
            # Cache miss or expired - call the function
            logger.debug(f"Cache miss for {cache_key} - fetching fresh data")
            result = await func(*args, **kwargs)
            
            # Cache the result
            cache[cache_key] = (now, result)
            return result
            
        return wrapper
    return decorator

# Initialize FastAPI app
app = FastAPI(
    title="Animal Humane API",
    description="API for shelter dog tracking and analytics",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency injection
def get_elasticsearch_service() -> ElasticsearchService:
    return ElasticsearchService()

def get_dog_service(es_service: ElasticsearchService = Depends(get_elasticsearch_service)) -> DogService:
    return DogService(es_service)

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=APIResponse.error_response("Internal server error").dict()
    )

# Health check
@app.get("/health")
async def health_check():
    return APIResponse.success_response({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.get("/api/cache/status")
async def get_cache_status():
    """Get cache status for monitoring"""
    now = datetime.now()
    cache_status = {}
    
    for key, (timestamp, data) in cache.items():
        age = now - timestamp
        is_expired = age >= CACHE_DURATION
        cache_status[key] = {
            "age_seconds": age.total_seconds(),
            "age_minutes": age.total_seconds() / 60,
            "expires_in_seconds": max(0, (CACHE_DURATION - age).total_seconds()),
            "is_expired": is_expired,
            "cached_at": timestamp.isoformat(),
            "data_size": len(str(data)) if data else 0
        }
    
    return APIResponse.success_response({
        "cache_duration_minutes": CACHE_DURATION.total_seconds() / 60,
        "cached_endpoints": list(cache.keys()),
        "cache_status": cache_status
    })

@app.post("/api/cache/clear")
async def clear_cache():
    """Clear all cached data (admin function)"""
    global cache
    cache.clear()
    return APIResponse.success_response({"message": "Cache cleared successfully"})


@app.post("/api/cache/refresh")
async def refresh_cache(request: Request, key: str = Query(...)):
    """Refresh a specific cache key (internal use only).

    Authorization:
      - If `config.api.internal_auth_token` is set, require header `X-Internal-Token` to match.
      - Otherwise, allow only requests originating from localhost (127.0.0.1 or ::1).
    """
    try:
        # Authorization
        token = config.api.internal_auth_token
        header_token = request.headers.get("X-Internal-Token")
        client_host = request.client.host if request.client else None

        authorized = False
        if token:
            if header_token and header_token == token:
                authorized = True
        else:
            if client_host in ("127.0.0.1", "::1", "localhost"):
                authorized = True

        if not authorized:
            raise HTTPException(status_code=403, detail="Forbidden")

        # Remove cache entry and re-populate by calling the associated function
        cache.pop(key, None)

        # Map known keys to functions to repopulate
        if key == "missing_dogs":
            # Call the missing-dogs reader which will cache via decorator
            await get_missing_dogs()
        elif key == "diff_analysis":
            from services.elasticsearch_service import ElasticsearchService
            es_service = ElasticsearchService()
            await es_service.get_diff_analysis()
        elif key == "overview":
            # trigger overview computation
            # Note: get_overview depends on DogService; we call the endpoint indirectly
            pass

        return APIResponse.success_response({"key": key, "refreshed": True})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing cache key {key}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug/es-connection")
async def debug_es_connection():
    """Debug endpoint to test Elasticsearch connection"""
    try:
        from config import config
        import os
        es_host = config.elasticsearch.host
        env_host = os.getenv("ELASTICSEARCH_HOST")
        return APIResponse.success_response({
            "config_host": es_host,
            "env_host": env_host,
            "all_env": dict(os.environ)
        })
    except Exception as e:
        return APIResponse.error_response(f"Debug error: {str(e)}")

# API Routes
@app.get("/api/overview", response_model=APIResponse)
@cached("overview")
async def get_overview(dog_service: DogService = Depends(get_dog_service)):
    """Get shelter overview statistics"""
    try:
        stats = await dog_service.get_overview_stats()
        return APIResponse.success_response(stats)
    except Exception as e:
        logger.error(f"Error getting overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/new-dogs-this-week", response_model=APIResponse)
async def get_new_dogs_this_week(es_service: ElasticsearchService = Depends(get_elasticsearch_service)):
    """Get names of new dogs this week"""
    try:
        dog_names = await es_service.get_new_dog_names_this_week()
        return APIResponse.success_response({"count": len(dog_names), "names": dog_names})
    except Exception as e:
        logger.error(f"Error getting new dogs this week: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dogs", response_model=APIResponse)
async def get_dogs(dog_service: DogService = Depends(get_dog_service)):
    """Get all available dogs"""
    try:
        dogs = await dog_service.get_available_dogs()
        return APIResponse.success_response(dogs)
    except Exception as e:
        logger.error(f"Error getting dogs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/live_population", response_model=APIResponse)
@cached("live_population")
async def get_live_population(dog_service: DogService = Depends(get_dog_service)):
    """Get live population of available dogs"""
    try:
        dogs = await dog_service.get_available_dogs()
        return APIResponse.success_response(dogs)
    except Exception as e:
        logger.error(f"Error getting live population: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dogs/{dog_id}", response_model=APIResponse)
async def get_dog(dog_id: int, dog_service: DogService = Depends(get_dog_service)):
    """Get a specific dog by ID"""
    try:
        dog = await dog_service.get_dog_by_id(dog_id)
        if not dog:
            raise HTTPException(status_code=404, detail="Dog not found")
        return APIResponse.success_response(dog)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dog {dog_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/dogs/{dog_id}", response_model=APIResponse)
async def update_dog(
    dog_id: int, 
    dog_update: DogUpdate,
    dog_service: DogService = Depends(get_dog_service)
):
    """Update a dog's information"""
    try:
        result = await dog_service.update_dog(dog_id, dog_update)
        return APIResponse.success_response(result, "Dog updated successfully")
    except Exception as e:
        logger.error(f"Error updating dog {dog_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/adoptions", response_model=APIResponse)
async def get_adoptions(dog_service: DogService = Depends(get_dog_service)):
    """Get recent adoptions"""
    try:
        adoptions = await dog_service.get_recent_adoptions()
        return APIResponse.success_response(adoptions)
    except Exception as e:
        logger.error(f"Error getting adoptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/missing-dogs", response_model=APIResponse)
@cached("missing_dogs")
async def get_missing_dogs():
    """Return the missing dogs list parsed from react-app/public/missing_dogs.txt
    If the file is not found, attempts to read a top-level missing_dogs.txt as a fallback.
    Response: list of {id: int, name: str}
    """
    try:
        project_root = Path(__file__).resolve().parents[1]
        candidate_paths = [
            project_root / 'react-app' / 'public' / 'missing_dogs.txt',
            project_root / 'missing_dogs.txt'
        ]

        file_path = None
        for p in candidate_paths:
            if p.exists():
                file_path = p
                break

        if not file_path:
            # No file available - return empty list
            return APIResponse.success_response([])

        text = file_path.read_text(encoding='utf-8')
        dogs = []
        for line in text.splitlines():
            line = line.strip()
            if not line or line.lower().startswith('missing dogs'):
                continue
            m = re.match(r'^(\d+):\s*(.+)$', line)
            if m:
                dog_id = int(m.group(1))
                name = m.group(2).strip()
                dogs.append({"id": dog_id, "name": name})

        return APIResponse.success_response(dogs)

    except Exception as e:
        logger.error(f"Error reading missing_dogs.txt: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/insights", response_model=APIResponse)
@cached("insights")
async def get_insights(dog_service: DogService = Depends(get_dog_service)):
    """Get insights and analytics"""
    try:
        insights = await dog_service.get_insights()
        return APIResponse.success_response(insights)
    except Exception as e:
        logger.error(f"Error getting insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dog-origins", response_model=APIResponse)
@cached("dog_origins")
async def get_dog_origins(dog_service: DogService = Depends(get_dog_service)):
    """Get dog origin data for mapping"""
    try:
        origins = await dog_service.get_dog_origins()
        return APIResponse.success_response(origins)
    except Exception as e:
        logger.error(f"Error getting dog origins: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/weekly-age-group-adoptions", response_model=APIResponse)
@cached("weekly_age_group_adoptions")
async def get_weekly_age_group_adoptions(dog_service: DogService = Depends(get_dog_service)):
    """Get weekly age group adoptions"""
    try:
        data = await dog_service.get_weekly_age_group_adoptions()
        return APIResponse.success_response(data)
    except Exception as e:
        logger.error(f"Error getting weekly age group adoptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/length-of-stay", response_model=APIResponse)
async def get_length_of_stay(dog_service: DogService = Depends(get_dog_service)):
    """Get length of stay histogram distribution"""
    try:
        histogram_data = await dog_service.get_length_of_stay_data()
        return APIResponse.success_response(histogram_data)
    except Exception as e:
        logger.error(f"Error getting length of stay distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/diff-analysis", response_model=APIResponse)
@cached("diff_analysis")
async def get_diff_analysis(es_service: ElasticsearchService = Depends(get_elasticsearch_service)):
    """Get diff analysis data (new, returned, adopted, trial, unlisted dogs)"""
    try:
        data = await es_service.get_diff_analysis()
        return APIResponse.success_response(data)
    except Exception as e:
        logger.error(f"Error getting diff analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/missing-dogs", response_model=APIResponse)
async def get_missing_dogs():
    """Return the missing dogs list parsed from missing_dogs.txt (if present)

    The scheduler writes the current file to react-app/public/missing_dogs.txt. This
    endpoint attempts to find the most likely file locations and parse it into JSON.
    """
    try:
        candidates = [
            os.path.join(os.getcwd(), 'react-app', 'public', 'missing_dogs.txt'),
            os.path.join(os.path.dirname(__file__), '..', 'react-app', 'public', 'missing_dogs.txt'),
            os.path.join(os.getcwd(), 'missing_dogs.txt')
        ]

        file_path = None
        for p in candidates:
            if os.path.exists(p):
                file_path = p
                break

        if not file_path:
            logger.info("missing_dogs.txt not found in known locations")
            return APIResponse.success_response([])

        dogs = []
        with open(file_path, 'r', encoding='utf-8') as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith('Missing dogs'):
                    continue
                m = re.match(r'^(\d+):\s*(.+)$', line)
                if m:
                    dog_id = int(m.group(1))
                    name = m.group(2).strip()
                    dogs.append({
                        'id': dog_id,
                        'name': name,
                        'url': f'https://new.shelterluv.com/embed/animal/{dog_id}'
                    })
        return APIResponse.success_response(dogs)

    except Exception as e:
        logger.error(f"Error reading missing_dogs.txt: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run_document_updates", response_model=APIResponse)
async def run_document_updates(dog_service: DogService = Depends(get_dog_service)):
    """Run document updates (admin function)"""
    try:
        result = await dog_service.run_updates()
        return APIResponse.success_response(result, "Updates completed successfully")
    except Exception as e:
        logger.error(f"Error running updates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=config.api.host,
        port=config.api.port,
        reload=config.api.debug
    )