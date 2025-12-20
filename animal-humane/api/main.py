"""
Refactored FastAPI application with improved structure
"""
from datetime import datetime
from typing import List
import traceback

from fastapi import FastAPI, HTTPException, Depends, status
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

# Setup logging
logger = setup_logger("api")

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
async def get_overview(dog_service: DogService = Depends(get_dog_service)):
    """Get shelter overview statistics"""
    try:
        stats = await dog_service.get_overview_stats()
        return APIResponse.success_response(stats)
    except Exception as e:
        logger.error(f"Error getting overview: {e}")
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

@app.get("/api/insights", response_model=APIResponse)
async def get_insights(dog_service: DogService = Depends(get_dog_service)):
    """Get insights and analytics"""
    try:
        insights = await dog_service.get_insights()
        return APIResponse.success_response(insights)
    except Exception as e:
        logger.error(f"Error getting insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dog-origins", response_model=APIResponse)
async def get_dog_origins(dog_service: DogService = Depends(get_dog_service)):
    """Get dog origin data for mapping"""
    try:
        origins = await dog_service.get_dog_origins()
        return APIResponse.success_response(origins)
    except Exception as e:
        logger.error(f"Error getting dog origins: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/weekly-age-group-adoptions", response_model=APIResponse)
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
async def get_diff_analysis(es_service: ElasticsearchService = Depends(get_elasticsearch_service)):
    """Get diff analysis data (new, returned, adopted, trial, unlisted dogs)"""
    try:
        data = await es_service.get_diff_analysis()
        return APIResponse.success_response(data)
    except Exception as e:
        logger.error(f"Error getting diff analysis: {e}")
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