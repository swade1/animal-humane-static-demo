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
        # Temporary debug: log counts to help diagnose discrepancy between service and API output
        try:
            adopted_count = len(data.get('adopted_dogs', [])) if data else 0
            trial_count = len(data.get('trial_adoption_dogs', [])) if data else 0
            logger.info(f"DEBUG: API diff_analysis computed: adopted={adopted_count}, trial={trial_count}")
        except Exception:
            logger.info("DEBUG: API diff_analysis computed: could not determine counts")
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


# Debug endpoint: return raw diff analysis from ElasticsearchService (bypass cache and models)
@app.get("/api/debug/raw-diff")
async def debug_raw_diff():
    try:
        from services.elasticsearch_service import ElasticsearchService
        es_service = ElasticsearchService()
        # Run and return raw result
        result = await es_service.get_diff_analysis()
        return result
    except Exception as e:
        logger.error(f"Error in debug_raw_diff: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Admin endpoints for manual overrides of today's Adopted list
@app.get("/api/admin/overrides/adopted")
async def get_adopted_overrides():
    try:
        import os, json
        path = os.path.join(os.getcwd(), 'overrides', 'adopted_today.json')
        if not os.path.exists(path):
            return APIResponse.success_response([])
        with open(path, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        return APIResponse.success_response(data)
    except Exception as e:
        logger.error(f"Error reading adopted overrides: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/overrides/adopted")
async def add_adopted_override(item: dict):
    try:
        import os, json
        path = os.path.join(os.getcwd(), 'overrides')
        os.makedirs(path, exist_ok=True)
        file_path = os.path.join(path, 'adopted_today.json')
        data = []
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as fh:
                data = json.load(fh) or []
        data.append(item)
        with open(file_path, 'w', encoding='utf-8') as fh:
            json.dump(data, fh)
        return APIResponse.success_response(data)
    except Exception as e:
        logger.error(f"Error adding adopted override: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/admin/overrides/adopted")
async def remove_adopted_override(dog_id: int = Query(...)):
    try:
        import os, json
        path = os.path.join(os.getcwd(), 'overrides', 'adopted_today.json')
        if not os.path.exists(path):
            return APIResponse.success_response([])
        with open(path, 'r', encoding='utf-8') as fh:
            data = json.load(fh) or []
        new = [d for d in data if not ((isinstance(d, dict) and d.get('dog_id') == dog_id) or (isinstance(d, int) and d == dog_id))]
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(new, fh)
        return APIResponse.success_response(new)
    except Exception as e:
        logger.error(f"Error removing adopted override: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Debug endpoint: inspect intermediate values used for diff analysis for Prince Charming
@app.get("/api/debug/inspect-prince")
async def debug_inspect_prince():
    """Return intermediate values to help trace why Prince Charming is not in adopted list"""
    try:
        from services.elasticsearch_service import ElasticsearchService
        es_service = ElasticsearchService()

        # Get current availables
        availables = await es_service.get_current_availables()
        avail_count = len(availables)
        prince_in_avail = any(d.get('id') == 212434888 or d.get('dog_id') == 212434888 for d in availables)

        # Get most recent index
        idx = await es_service.get_most_recent_index()

        # Get dog_groups for a trial record
        trial_record = {'name': 'Prince Charming', 'dog_id': 212434888, 'url': 'https://new.shelterluv.com/embed/animal/212434888', 'location': 'Trial Adoption'}
        dog_groups_for_trial = await es_service.get_dog_groups([trial_record], idx)

        # Full diff
        full_diff = await es_service.get_diff_analysis()

        # Run a direct "recent adopted" query (same as handler) to see raw hits
        from datetime import datetime, timedelta
        current_date = idx.split('animal-humane-')[1].split('-')[0]
        current_dt = datetime.strptime(current_date, '%Y%m%d')
        cutoff_dt = current_dt - timedelta(days=8)
        cutoff_str = cutoff_dt.strftime('%Y-%m-%dT%H:%M:%S')
        recent_query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"status": "adopted"}},
                        {"range": {"timestamp": {"gte": cutoff_str}}}
                    ]
                }
            },
            "_source": ["name", "id", "url", "location", "status", "timestamp"],
            "size": 1000
        }

        raw_recent_resp = es_service.handler.es.search(index='animal-humane-*', body=recent_query)
        raw_recent_ids = [hit.get('_source', {}).get('id') for hit in raw_recent_resp.get('hits', {}).get('hits', [])][:50]

        # Run the verification search used for trial verification
        verify_body = {
            "sort": [{"timestamp": {"order": "desc"}}],
            "query": {"term": {"id": {"value": 212434888}}},
            "_source": ["name", "id", "status", "timestamp", "url", "location"],
            "size": 1
        }
        verify_resp = es_service.handler.es.search(index='animal-humane-*', body=verify_body)
        verify_hits = verify_resp.get('hits', {}).get('hits', [])
        verify_top = None
        if verify_hits:
            verify_top = verify_hits[0]

        return APIResponse.success_response({
            'avail_count': avail_count,
            'prince_in_avail': prince_in_avail,
            'most_recent_index': idx,
            'dog_groups_for_trial': dog_groups_for_trial,
            'full_diff_has_prince': any(d.get('dog_id') == 212434888 or d.get('id') == 212434888 or d.get('name') == 'Prince Charming' for d in full_diff.get('adopted_dogs', [])),
            'full_diff_sample_adopted': full_diff.get('adopted_dogs', [])[:10],
            'raw_recent_ids_sample': raw_recent_ids,
            'verify_top': verify_top
        })
    except Exception as e:
        logger.error(f"Error in debug_inspect_prince: {e}")
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