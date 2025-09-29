"""
Improved FastAPI application with better structure
Maintains all existing endpoints while using the new architecture
"""
from datetime import datetime
from typing import List, Dict, Any
import traceback

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel

from services.dog_service import DogService
from services.elasticsearch_service import ElasticsearchService
from shelterdog_tracker.elasticsearch_handler import ElasticsearchHandler
from shelterdog_tracker.shelter_scraper import ShelterScraper

# Initialize FastAPI app
app = FastAPI(
    title="Animal Humane API",
    description="API for shelter dog tracking and analytics",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class DogUpdate(BaseModel):
    index: str | None = None
    name: str | None = None
    location: str | None = None
    origin: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    age_group: str | None = None
    birthdate: str | None = None
    bite_quarantine: int | None = None
    breed: str | None = None
    secondary_breed: str | None = None
    color: str | None = None
    id: int | None = None
    intake_date: str | None = None
    length_of_stay_days: int | None = None
    returned: int | None = None
    timestamp: str | None = None
    url: str | None = None
    weight_group: str | None = None
    status: str | None = None

# Dependency injection
def get_handler():
    """Get Elasticsearch handler - maintains compatibility with existing code"""
    return ElasticsearchHandler(host="http://localhost:9200", index_name="animal-humane-latest")

def get_elasticsearch_service() -> ElasticsearchService:
    return ElasticsearchService()

def get_dog_service(es_service: ElasticsearchService = Depends(get_elasticsearch_service)) -> DogService:
    return DogService(es_service)

# Utility functions (migrated from original)
def scrape_and_push():
    """
    Function to scrape current data and push to Elasticsearch.
    """
    today_str = datetime.now().strftime('%Y%m%d')
    today_time = datetime.now().strftime('%H%M') 
    scraper = ShelterScraper(main_url="https://animalhumanenm.org/adopt/adoptable-dogs/")
    index_name = f"animal-humane-{today_str}-{today_time}"
    handler = ElasticsearchHandler(host="http://localhost:9200", index_name=index_name)
    handler.es.indices.create(index=index_name, ignore=400)
    all_dogs = scraper.scrape_all_dogs()
    handler.push_dogs_to_elasticsearch(all_dogs)
    
    # Update alias
    handler.es.indices.update_aliases(body={
        "actions": [
            {"remove": {"index": "*", "alias": "animal-humane-latest"}},
            {"add": {"index": index_name, "alias": "animal-humane-latest"}},
        ]
    })

    return {"message": f"Scraped data pushed to index {index_name}"}

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print("Validation error: ", exc)
    print("Request body received that failed:", await request.body())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    print(f"Unhandled exception: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# API Routes - maintaining all existing endpoints

@app.get("/api/overview")
async def get_overview(dog_service: DogService = Depends(get_dog_service)):
    """Get shelter overview statistics"""
    try:
        return await dog_service.get_overview_stats()
    except Exception as e:
        print(f"Error in get_overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/live_population")
async def live_population(dog_service: DogService = Depends(get_dog_service)):
    """Get live population data"""
    try:
        availables = await dog_service.get_available_dogs()
        if availables is None:
            availables = []
        print(f"type of availables is: {type(availables)}")
        return availables
    except Exception as e:
        print(f"Error in live_population: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dogs", response_model=List[dict])
async def get_dogs(dog_service: DogService = Depends(get_dog_service)):
    """Get all available dogs"""
    try:
        availables = await dog_service.get_available_dogs()
        if availables is None:
            availables = []
        print(f"type of availables is: {type(availables)}")
        return availables
    except Exception as e:
        print(f"Error in get_dogs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dogs/{dog_id}", response_model=dict)
async def get_dog(dog_id: int, dog_service: DogService = Depends(get_dog_service)):
    """Get a specific dog by ID"""
    try:
        res = await dog_service.get_dog_by_id(dog_id)
        if not res:
            raise HTTPException(status_code=404, detail="Dog not found")
        return res
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_dog: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/dogs/{dog_id}")
async def update_dog(dog_id: str, dog_update: DogUpdate, handler: ElasticsearchHandler = Depends(get_handler)):
    """Update a dog's information"""
    print(f"update_dog has been called with dog_id: {dog_id} and dog_update: {dog_update}")
    try:
        data = dog_update.dict(exclude_unset=True)
        print(f"Received data for dog {dog_id}:", data)
        print(f"Index: {data.get('index')}")
        
        if 'index' not in data or not data['index']:
            raise HTTPException(status_code=400, detail="Index is required for update")
        
        update_body = {"doc": data}
        handler.es.update(index=data['index'], id=dog_id, body=update_body)
        return {"result": "updated"}
    except Exception as e:
        print("Exception during update:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to update dog")

@app.get("/api/dogs/{dog_id}/latest_index")
def get_latest_index(dog_id: int, handler: ElasticsearchHandler = Depends(get_handler)):
    """Get the latest index for a specific dog"""
    print("********************** Function get_latest_index has been called")
    try:
        query = {
            "query": {"match": {"id": dog_id}},
            "size": 1,
            "_source": False,
            "sort": [{"_index": {"order": "desc"}}]
        }
        res = handler.es.search(index="animal-humane-*", body=query)
        hits = res["hits"]["hits"]
        print(f"Hits after query for latest_index are: {hits}")
        if hits:
            return {"index": hits[0]["_index"]}
        else:
            return {"index": None}
    except Exception as e:
        print(f"Error in get_latest_index: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/adoptions")
async def get_adoptions(dog_service: DogService = Depends(get_dog_service)):
    """Get recent adoptions"""
    print("adoption_movement has been called")
    try:
        return await dog_service.get_recent_adoptions()
    except Exception as e:
        print(f"Error in get_adoptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/insights")
async def get_insights(dog_service: DogService = Depends(get_dog_service)):
    """Get insights and analytics"""
    try:
        return await dog_service.get_insights()
    except Exception as e:
        print(f"Error in get_insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/weekly-age-group-adoptions")
async def get_weekly_age_group_adoptions(dog_service: DogService = Depends(get_dog_service)):
    """Get weekly age group adoptions"""
    try:
        return await dog_service.get_weekly_age_group_adoptions()
    except Exception as e:
        print(f"Error in get_weekly_age_group_adoptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dog-origins-map")
async def get_dog_origin_map(dog_service: DogService = Depends(get_dog_service)):
    """Get dog origin map data"""
    try:
        result = await dog_service.get_adoption_percentages_per_origin()
        for res in result:
            print(res)
        return result
    except Exception as e:
        print(f"Error in get_dog_origin_map: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dog-origins")
async def get_dog_origins(dog_service: DogService = Depends(get_dog_service)):
    """
    Returns a list of dictionaries with origin, latitude, longitude, and count
    for map and shelter count bar chart visualizations. 
    """
    try:
        print("Calling dog_service.get_dog_origins()")  
        origins = await dog_service.get_dog_origins()
        print(f"Inside main_improved.py, returned origins from get_dog_origins() is: {origins}")
        print(f"Returning results for map: {origins}")
        return origins
    except Exception as e:
        print(f"Error in get_dog_origins: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run_document_updates")
async def api_run_updates(dog_service: DogService = Depends(get_dog_service)):
    """Endpoint to update documents (should be called as needed)."""
    try:
        return await dog_service.run_document_updates()
    except Exception as e:
        print(f"Error in api_run_updates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/animal_updates_text", response_class=PlainTextResponse)
async def api_animal_updates_text(dog_service: DogService = Depends(get_dog_service)):
    """Get animal updates as formatted text"""
    try:
        results = await dog_service.run_animal_updates()
        pretty_text = await dog_service.format_dog_groups(results)
        print(pretty_text)  # This prints it to the server logs/console
        return pretty_text
    except Exception as e:
        print(f"Error in api_animal_updates_text: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Animal Humane API"
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting Animal Humane API with improved architecture...")
    uvicorn.run(
        "main_improved:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )