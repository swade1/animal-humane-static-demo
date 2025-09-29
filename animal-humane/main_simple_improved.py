"""
Simple improved version of main_new.py with better error handling
Maintains exact same structure but with improvements
"""
from datetime import datetime
import json
import traceback

from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan
from fastapi import FastAPI, Depends, APIRouter, HTTPException, Request, status, Query
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional

from output_utils import print_dog_groups
from shelterdog_tracker.shelter_scraper import ShelterScraper
from shelterdog_tracker.elasticsearch_handler import ElasticsearchHandler

# Initialize FastAPI app with better configuration
app = FastAPI(
    title="Animal Humane API",
    description="API for shelter dog tracking and analytics",
    version="1.0.0"
)

router = APIRouter()

# Improved CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

INDEX_NAME = "animal-humane-latest"

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

def get_handler():
    """Create & return a handler instance with error handling"""
    try:
        # Use port 9201 for local Elasticsearch with historical data
        handler = ElasticsearchHandler(host="http://localhost:9201", index_name="animal-humane-latest")
        # Test connection but don't fail startup if it's not ready
        try:
            handler.es.ping()
        except Exception as ping_error:
            print(f"Warning: Elasticsearch not ready: {ping_error}")
        return handler
    except Exception as e:
        print(f"Error creating Elasticsearch handler: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")

def scrape_and_push():
    """
    Function to scrape current data and push to Elasticsearch.
    Enhanced with better error handling.
    """
    try:
        today_str = datetime.now().strftime('%Y%m%d')
        today_time = datetime.now().strftime('%H%M') 
        scraper = ShelterScraper(main_url="https://animalhumanenm.org/adopt/adoptable-dogs/")
        index_name = f"animal-humane-{today_str}-{today_time}"
        handler = ElasticsearchHandler(host="http://localhost:9200", index_name=index_name)
        
        # Create index with error handling
        handler.es.indices.create(index=index_name, ignore=400)
        all_dogs = scraper.scrape_all_dogs()
        handler.push_dogs_to_elasticsearch(all_dogs)
        
        # Update alias with error handling
        handler.es.indices.update_aliases(body={
            "actions": [
                {"remove": {"index": "*", "alias": "animal-humane-latest"}},
                {"add": {"index": index_name, "alias": "animal-humane-latest"}},
            ]
        })

        return {"message": f"Scraped data pushed to index {index_name}"}
    except Exception as e:
        print(f"Error in scrape_and_push: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

def animal_updates(handler):
    """Enhanced animal updates with better error handling"""
    try:
        availables = handler.get_current_availables()
        idx = handler.get_most_recent_index()
        results = handler.get_dog_groups(availables, idx)
        new_dogs = handler.get_new_dogs()

        # Add new_dogs to results before printing
        if "new_dogs" not in results:
            results["new_dogs"] = []
        results["new_dogs"].extend(new_dogs.get("new_dogs", []))
        print_dog_groups(results)
        return results
    except Exception as e:
        print(f"Error in animal_updates: {e}")
        traceback.print_exc()
        raise

def run_updates(handler, results):
    """Enhanced run_updates with better error handling"""
    try:
        handler.update_dogs(results)
        return {"detail": "Documents updated."}
    except Exception as e:
        print(f"Error in run_updates: {e}")
        traceback.print_exc()
        raise

def format_dog_groups(dog_groups):
    """Format dog groups for display - unchanged"""
    lines = []

    lines.append("New Dogs:")
    for dog in dog_groups.get('new_dogs', []):
        name = dog.get('name', 'Unnamed Dog')
        url = dog.get('url', 'No URL')
        lines.append(f"  {name} - {url}")
    lines.append("")

    lines.append("Adopted/Reclaimed Dogs:")
    for dog in dog_groups.get('adopted_dogs', []):
        name = dog.get('name', 'Unnamed Dog')
        url = dog.get('url', 'No URL')
        lines.append(f"  {name} - {url}")
    lines.append("")

    lines.append("Trial Adoptions:")
    for dog in dog_groups.get('trial_adoption_dogs', []):
        name = dog.get('name', 'Unnamed Dog')
        url = dog.get('url', 'No URL')
        lines.append(f"  {name} - {url}")
    lines.append("")

    lines.append("Other Unlisted Dogs:")
    for dog in dog_groups.get('other_unlisted_dogs', []):
        name = dog.get('name', 'Unnamed Dog')
        url = dog.get('url', 'No URL')
        lines.append(f"  {name} - {url}")
    lines.append("")

    return "\n".join(lines)

def log_overview_output(total_dogs, new, adopted, trial):
    """Enhanced logging with better error handling"""
    try:
        print("*********************** log_overview_output has been called")
        handler = get_handler()    
        today_str = datetime.now().strftime('%Y%m%d')
        idx_name = f"logging-{today_str}"

        mapping = {
            "mappings": {
                "properties": {
                    "timestamp": {"type": "date", "format": "strict_date_optional_time||epoch_millis"},
                    "total_dogs": {"type": "integer"},
                    "new_this_week": {"type": "integer"},
                    "adopted_this_week": {"type": "integer"},
                    "trial_adoptions": {"type": "integer"},
                    "avg_length_of_stay": {"type": "integer"}
                }
            }
        }
        
        handler.create_index(idx_name, mapping)
        doc = {
            "timestamp": datetime.now().isoformat(),
            "total_dogs": total_dogs,
            "new_this_week": new,
            "adopted_this_week": adopted,
            "trial_adoptions": trial
        }
        handler.push_doc_to_elastic(idx_name, doc)
    except Exception as e:
        print(f"Error in log_overview_output: {e}")
        # Don't raise here as this is just logging

# Enhanced exception handlers
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
        content={"detail": "Internal server error", "error": str(exc)}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        handler = get_handler()
        # Test Elasticsearch connection
        handler.es.ping()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "elasticsearch": "connected"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        )

@app.post("/api/run-diff-analysis")
async def run_diff_analysis_manual():
    """Manually trigger diff analysis"""
    try:
        from scheduler.diff_analyzer import DiffAnalyzer
        
        analyzer = DiffAnalyzer(output_dir="diff_reports")
        results = analyzer.analyze_differences()
        
        if results:
            return {
                "success": True,
                "message": "Diff analysis completed",
                "summary": results['summary'],
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "message": "No differences found or insufficient data",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        print(f"Error in manual diff analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# API Routes - All your existing endpoints with enhanced error handling

@app.post("/run_document_updates")
def api_run_updates(handler: ElasticsearchHandler = Depends(get_handler)):
    """Endpoint to update documents with enhanced error handling"""
    try:
        results = animal_updates(handler)
        update_result = run_updates(handler, results)
        return {"update_result": update_result, "animal_updates": results}
    except Exception as e:
        print(f"Error in api_run_updates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/animal_updates_text", response_class=PlainTextResponse)
def api_animal_updates_text(handler: ElasticsearchHandler = Depends(get_handler)):
    """Get animal updates as text with enhanced error handling"""
    try:
        results = animal_updates(handler)
        pretty_text = format_dog_groups(results)
        print(pretty_text)
        return pretty_text
    except Exception as e:
        print(f"Error in api_animal_updates_text: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/overview")
def get_overview():
    """Get overview with enhanced error handling"""
    try:
        handler = get_handler()
        
        availables = handler.get_current_availables()
        idx = handler.get_most_recent_index()
        results = handler.get_dog_groups(availables, idx)
        
        print(f"results in main_simple_improved.py: {results}")
        
        age_groups = handler.get_age_groups(idx)
        
        print("Unlisted Dogs") 
        for dog in results['other_unlisted_dogs']:
            print(dog["name"])

        total_unlisted = len(results['other_unlisted_dogs'])
        print(f"total_unlisted: {total_unlisted}")

        total_listed = handler.get_current_listed_count()
        total_listed_and_unlisted = total_listed + total_unlisted
        print(f"total_listed_and_unlisted: {total_listed_and_unlisted}")

        new_dog_count = handler.get_new_dog_count_this_week()
        _, _, _, _, adopted_dog_count = handler.get_adopted_dog_count_this_week() 
        trial_adoption_count = len(results['trial_adoption_dogs']) 

        print(f"total trial_adoption_count: {trial_adoption_count}")
        log_overview_output(total_listed + total_unlisted, new_dog_count, adopted_dog_count, trial_adoption_count)

        avgStay = handler.get_avg_length_of_stay()
        longest_resident = handler.get_longest_resident()
        print(f"longest_resident: {longest_resident}")

        return {
            "total": total_listed_and_unlisted - trial_adoption_count,
            "newThisWeek": new_dog_count,
            "adoptedThisWeek": adopted_dog_count,
            "trialAdoptions": trial_adoption_count,
            "ageGroups": age_groups,
            "avgStay": avgStay,
            "longestStay": longest_resident
        }
    except Exception as e:
        print(f"Error in get_overview: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/live_population")
async def live_population():
    """Get live population with enhanced error handling"""
    try:
        handler = get_handler()
        availables = handler.get_current_availables()
        if availables is None:
            availables = []
        print(f"type of availables is: {type(availables)}")
        return availables
    except Exception as e:
        print(f"Error in live_population: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dogs", response_model=List[dict])
async def get_dogs():
    """Get dogs with enhanced error handling"""
    try:
        handler = get_handler()
        availables = handler.get_current_availables()
        if availables is None:
            availables = []
        print(f"type of availables is: {type(availables)}")
        return availables
    except Exception as e:
        print(f"Error in get_dogs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dogs/{dog_id}", response_model=dict)
async def get_dog(dog_id: int):
    """Get dog by ID with enhanced error handling"""
    try:
        handler = get_handler()
        res = handler.get_dog_by_id(dog_id) 
        if not res:
            raise HTTPException(status_code=404, detail="Dog not found")
        return res
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_dog: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/dogs/{dog_id}")
async def update_dog(dog_id: str, dog_update: DogUpdate):
    """Update dog with enhanced error handling"""
    print(f"update_dog called with dog_id: {dog_id}")
    try:
        data = dog_update.dict(exclude_unset=True)
        print(f"Received data for dog {dog_id}:", data)
        
        handler = get_handler()
        
        if 'index' not in data or not data['index']:
            raise HTTPException(status_code=400, detail="Index is required for update")
        
        update_body = {"doc": data}
        handler.es.update(index=data['index'], id=dog_id, body=update_body)
        return {"result": "updated"}
    except HTTPException:
        raise
    except Exception as e:
        print("Exception during update:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to update dog")

@app.get("/api/dogs/{dog_id}/latest_index")
def get_latest_index(dog_id: int):
    """Get latest index with enhanced error handling"""
    try:
        handler = get_handler()
        print("********************** Function get_latest_index has been called")
        query = {"query": {"match": {"id": dog_id}}, "size": 1, "_source": False, "sort": [{"_index": {"order": "desc"}}]}
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
def get_adoptions():
    """Get adoptions with enhanced error handling"""
    try:
        print("adoption_movement has been called")
        handler = get_handler()
        names, dates, urls, los, _ = handler.get_adopted_dog_count_this_week()
        print(f"dates returned from get_adopted_dog_count_this_week: {dates}")
        
        date_strings = [
            datetime.strptime(date, '%Y-%m-%dT%H:%M:%S%z')
            for date in dates if date
        ]
        
        adoptions = [
            {"name": name, "date": date.strftime('%m/%d/%Y'), "url": url, "los": los} 
            for name, date, url, los in zip(names, date_strings, urls, los)
        ]

        return adoptions
    except Exception as e:
        print(f"Error in get_adoptions: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/insights")
def get_insights():
    """Get insights with enhanced error handling"""
    try:
        handler = get_handler()
        daily_adoptions = handler.get_adoptions_per_day()
        return {"dailyAdoptions": daily_adoptions}
    except Exception as e:
        print(f"Error in get_insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/weekly-age-group-adoptions")
def get_weekly_age_group_adoptions():
    """Get weekly age group adoptions with enhanced error handling"""
    try:
        handler = get_handler()
        result = handler.get_weekly_age_group_adoptions()
        return result
    except Exception as e:
        print(f"Error in get_weekly_age_group_adoptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dog-origins-map")
def get_dog_origin_map():
    """Get dog origin map with enhanced error handling"""
    try:
        handler = get_handler()
        result = handler.get_adoption_percentages_per_origin()
        for res in result:
            print(res)
        return result
    except Exception as e:
        print(f"Error in get_dog_origin_map: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dog-origins")
def get_dog_origins():
    """Get dog origins with enhanced error handling"""
    try:
        handler = get_handler()
        print("Calling handler.get_origins()")  
        origins = handler.get_origins()
        
        # Debug: Check if Bayard is in the API response
        bayard_in_response = any("Bayard" in origin.get('origin', '') for origin in origins)
        clayton_in_response = any("Clayton" in origin.get('origin', '') for origin in origins)
        
        print(f"API RESPONSE - Total origins: {len(origins)}")
        print(f"API RESPONSE - Bayard Animal Control included: {bayard_in_response}")
        print(f"API RESPONSE - Clayton included: {clayton_in_response}")
        
        # Print the specific entries for debugging
        for origin in origins:
            if "Bayard" in origin.get('origin', '') or "Clayton" in origin.get('origin', ''):
                print(f"API RESPONSE ITEM: {origin}")
        
        return origins
    except Exception as e:
        print(f"Error in get_dog_origins: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("Starting Animal Humane API - Simple Improved Version")
    uvicorn.run(
        "main_simple_improved:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )