from datetime import datetime
import json

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
# In your main.py, ensure this router is included!




app = FastAPI()
router = APIRouter()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # or ["*"] to allow all, but restrict in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

INDEX_NAME = f"animal-humane-latest"

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

# Pydantic model for update payload validation
#class DogUpdate(BaseModel):
#    origin: Optional[str]
#    latitude: Optional[float]
#    longitude: Optional[float]

def get_handler():
    # Create & return a handler instance appropriate for your cluster/config
    return ElasticsearchHandler(host="http://localhost:9200", index_name="animal-humane-latest")

#@app.get("/animals")
#def get_animals(status: str = None):
#    """
#    API endpoint to get a list of animals.
#    Optionally filter by status (e.g., 'adopted', 'available')
#    """
#    try: 
#        # Assuming you have a method in your handler to search/filter animals by status
#        animals = handler.search_dogs(status=status)
#        return animals
#    except Exception as e:
#        raise HTTPException(status_code=500, detail=str(e))
#
#@app.get("/animals/{animal_name}")
#def get_animal(animal_name: str):
#    """
#    Get a single animal by name.
#    """
#   
#    try: 
#        animal = handler.get_dog_by_name(animal_name)
#        if not animal:
#            raise HTTPException(status_code=404, detail="Animal not found")
#        return animal
#    except Exception as e:
#        raise HTTPException(status_code=500, detail=str(e))

def scrape_and_push():
    """
    Function to scrape current data and push to Elasticsearch.
    You can call this manually, or schedule it outside of FastAPI.
    """
    today_str = datetime.now().strftime('%Y%m%d')
    today_time = datetime.now().strftime('%H%M') 
    scraper = ShelterScraper(main_url="https://animalhumanenm.org/adopt/adoptable-dogs/")
    index_name = f"animal-humane-{today_str}-{today_time}"
    handler = ElasticsearchHandler(host="http://localhost:9200", index_name=index_name)
    handler.es.indices.create(index=index_name, ignore=400)
    all_dogs = scraper.scrape_all_dogs()
    handler.push_dogs_to_elasticsearch(all_dogs)
    # Optional: update alias 'animal-humane-latest' to current index
    handler.es.indices.update_aliases(body={
        "actions": [
            {"remove": {"index": "*", "alias": "animal-humane-latest"}},
            {"add": {"index": index_name, "alias": "animal-humane-latest"}},
        ]
    })

    return {"message": f"Scraped data pushed to index {index_name}"}
    
def animal_updates(handler):
    availables = handler.get_current_availables()
    idx = handler.get_most_recent_index()
    results = handler.get_unlisted_dog_groups(availables, idx)
    new_dogs = handler.get_new_dogs()

    # add new_dogs to results before printing
    if "new_dogs" not in results:
        results["new_dogs"] = []
    results["new_dogs"].extend(new_dogs.get("new_dogs", []))
    print_dog_groups(results)
    return results

def run_updates(handler, results):
    handler.update_dogs(results)
    return {"detail": "Documents updated."}
# Optional: expose this function via API for manual trigger (be careful with this in production)
#@app.post("/scrape_and_update")
#def api_scrape_and_update():
#    return scrape_and_push()  
def format_dog_groups(dog_groups):
    lines = []

    lines.append("New Dogs:")
    for dog in dog_groups.get('new_dogs', []):
        name = dog.get('name', 'Unnamed Dog')
        url = dog.get('url', 'No URL')
        lines.append(f"  {name} - {url}")
    lines.append("")  # blank line

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
    print("*********************** log_overview_output has been called")
    handler = get_handler()    
    #get current date/time to use in index name
    today_str = datetime.now().strftime('%Y%m%d')
    idx_name = f"logging-{today_str}"

    mapping = {"mappings":{"properties":{"timestamp":{"type":"date","format":"strict_date_optional_time||epoch_millis"},"total_dogs":{"type":"integer"},"new_this_week":{"type":"integer"},"adopted_this_week":{"type":"integer"},"trial_adoptions":{"type":"integer"},"avg_length_of_stay": {"type": "integer"}}}}
    handler.create_index(idx_name, mapping)
    doc = {"timestamp": datetime.now().isoformat(),"total_dogs":total_dogs,"new_this_week":new,"adopted_this_week":adopted,"trial_adoptions":trial}
    handler.push_doc_to_elastic(idx_name, doc)

#@app.get("/animal_updates")
#def api_animal_updates(handler: ElasticsearchHandler = Depends(get_handler)):
#    """Endpoint to see animal updates."""
#    results = animal_updates(handler)
#    return results

@app.post("/run_document_updates")
def api_run_updates(handler: ElasticsearchHandler = Depends(get_handler)):
    """Endpoint to update documents (should be called as needed)."""
    results = animal_updates(handler)
    update_result = run_updates(handler, results)
    return {"update_result": update_result, "animal_updates": results}

# Returns output in a non-user friendly format but may need later
#@app.get("/animal_updates_formatted")
#def api_animal_updates_formatted(handler: ElasticsearchHandler = Depends(get_handler)):
#    results = animal_updates(handler)
#    pretty_text = format_dog_groups(results)
#    return {"formatted_animal_updates": pretty_text}

#@app.get("/animal_updates_text", response_class=PlainTextResponse)
#def api_animal_updates_text(handler: ElasticsearchHandler = Depends(get_handler)):
#    results = animal_updates(handler)
#    pretty_text = format_dog_groups(results)
#    return pretty_text

@app.get("/animal_updates_text", response_class=PlainTextResponse)
def api_animal_updates_text(handler: ElasticsearchHandler = Depends(get_handler)):
    results = animal_updates(handler)
    pretty_text = format_dog_groups(results)
    print(pretty_text)  # This prints it to the server logs/console
    return pretty_text

@app.get("/api/overview")
def get_overview():
    total_listed = 0
    total_unlisted = 0
    trial_adoption_count = 0
    total_puppies = 0
    total_seniors = 0
    total_adults = 0

    handler = get_handler()

    #use 'availables' to calculate total number of unlisted dogs
    #Not using the length of availables as the total unlisted
    #because it includes dogs in trial adoptions

    #get_current_availables does not use most current index and includes dogs that are
    #technically available but not on the site. (those in bite-quarantine, recent returns, etc)
    availables = handler.get_current_availables()

    idx = handler.get_most_recent_index()
    #unlisted_dogs are retrieved from the most current index
    #TODO: handler.get_unlisted_dog_groups no longer exists. 
    #Figure out what changes you made that broke this and fix it.
    #results = handler.get_unlisted_dog_groups(availables, idx)
    results = handler.get_dog_groups(availables, idx)
    print(f"results in main_new.py (line 239): {results}")

    #Instead of trying to shoehorn an aggregation by age_groups into an existing function
    #maybe I should just create a new function for returning that info.
    #[{'age_group': 'Adult', 'count': 29}, {'age_group': 'Puppy', 'count': 8}, {'age_group': 'Senior', 'count': 5}]
    age_groups = handler.get_age_groups(idx)

    print("Unlisted Dogs") 
    for dog in results['other_unlisted_dogs']:
        print(dog["name"])

    total_unlisted = len(results['other_unlisted_dogs'])
    print(f"total_unlisted: {total_unlisted}")

    total_listed = handler.get_current_listed_count()

    #Total number of dogs who are at the shelter that have been listed at least once on the website
    total_listed_and_unlisted = total_listed + total_unlisted
    print(f"total_listed_and_unlisted: {total_listed_and_unlisted}")

    ##retrieve number of new dogs
    new_dog_count = handler.get_new_dog_count_this_week()

    ##retrieve number of adopted dogs
    _, _, _, _, adopted_dog_count = handler.get_adopted_dog_count_this_week() 
    ##retrieve number of dogs in trial adoptions
    trial_adoption_count = len(results['trial_adoption_dogs']) 

    print(f"total trial_adoption_count: {trial_adoption_count}")
    log_overview_output(total_listed + total_unlisted, new_dog_count, adopted_dog_count, trial_adoption_count)

    avgStay = handler.get_avg_length_of_stay()
    longest_resident = handler.get_longest_resident()
    print(f"longest_resident in main_new.py: {longest_resident}")

    return {
        "total": total_listed_and_unlisted - trial_adoption_count,
        "newThisWeek": new_dog_count,
        "adoptedThisWeek": adopted_dog_count,
        "trialAdoptions": trial_adoption_count,
        "ageGroups": age_groups,
        "avgStay": avgStay,
        "longestStay":longest_resident
    }

@app.get("/api/live_population")
async def live_population():
    handler = get_handler()
    availables = handler.get_current_availables()
    if availables is None:
        availables = []
    print(f"type of availables is: {type(availables)}")
    return availables

#Start code for inline editing
#This is exactly the same code as the function above
@app.get("/api/dogs", response_model=List[dict])
async def get_dogs():
    handler = get_handler()
    availables = handler.get_current_availables()
    if availables is None:
        availables = []
    print(f"type of availables is: {type(availables)}")
    return availables

#GET
@app.get("/api/dogs/{dog_id}", response_model=dict)
async def get_dog(dog_id: int):
    handler = get_handler()
    try:
        res = handler.get_dog_by_id(dog_id) 
        return res
    except Exception:
        raise HTTPException(status_code=404, detail="Dog not found")

#PUT
@app.put("/api/dogs/{dog_id}")
async def update_dog(dog_id: str, dog_update: DogUpdate):
    print(f"update_dog has been called in main_new.py with dog_id: {dog_update} and dog_update: {DogUpdate}")
    data = dog_update.dict(exclude_unset=True)
    print(f"Received data for dog {dog_id}:", data)
    print(f"Index: {data['index']}")
    handler = get_handler()
    try:
        update_body = {"doc": data}
        #need to get the most current document or better, pass in the index.
        handler.es.update(index=data['index'], id=dog_id, body=update_body)
        return {"result": "updated"}
    except Exception as e:
        print("Exception during update:", e)
        traceback.print.exc()
        raise HTTPException(status_code=500, detail="Failed to update dog")

#End code for inline editing

@app.get("/api/dogs/{dog_id}/latest_index")
def get_latest_index(dog_id: int):
    handler = get_handler()
    print("********************** Function get_latest_index_has been called")
    query = {"query":{"match":{"id":dog_id}},"size":1,"_source":False,"sort":[{"_index":{"order":"desc"}}]}
    res = handler.es.search(index="animal-humane-*", body=query)
    hits = res["hits"]["hits"]
    print(f"Hits after query for latest_index are: {hits}")
    if hits:
        return {"index": hits[0]["_index"]}
    else:
        return {"index": None}

@app.get("/api/adoptions")
def get_adoptions():
    print("adoption_movement has been called")
    handler = get_handler()
    names, dates, urls, los, _ = handler.get_adopted_dog_count_this_week()
    print(f"dates returned from get_adopted_dog_count_this_week: {dates}")
    date_strings = [
        #datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ").strftime("%m/%d/%Y")
        datetime.strptime(date, '%Y-%m-%dT%H:%M:%S%z')
        for date in dates if date  # skip None values just in case
    ]
    #formatted_date = datetime.strftime('%m/%d/%Y')
    adoptions = [{"name": name, "date": date.strftime('%m/%d/%Y'), "url":url, "los":los} for name, date, url, los in zip(names, date_strings,urls,los)]

    return adoptions 

@app.get("/api/insights")
def get_insights():
    handler = get_handler()
    #moved to Overview tab
    #avgStay = handler.get_avg_length_of_stay() 
    #longest_resident = handler.get_longest_resident()
    daily_adoptions = handler.get_adoptions_per_day()
    

    return {
        #"avgStay": avgStay,
        #"longestStay": longest_resident, 
        "dailyAdoptions": daily_adoptions
    }

@app.get("/api/weekly-age-group-adoptions")
def get_weekly_age_group_adoptions():
    handler = get_handler()
    result = handler.get_weekly_age_group_adoptions()
    return result

#@app.get("/api/daily_adoptions")
#def get_daily_adoptions():
#    handler = get_handler()
#    chart_data = handler.get_adoptions_per_day()
#    return chart_data 

@app.get("/api/dog-origins-map")
def get_dog_origin_map():
    handler = get_handler()
    result = handler.get_adoption_percentages_per_origin()
    for res in result:
        print(res)

@app.get("/api/dog-origins")
def get_dog_origins():
    """
    Returns a list of dictionaries with origin, latitude, longitude, and count
    for map and shelter count bar chart visualizations. 
    """
    handler = get_handler()
    # Query all currently listed dogs 
    print("Calling handler.get_origins()")  
    origins = handler.get_origins()

    print(f"Inside main_new.py, returned origins from get_origins() is: {origins}")
    #Returned data in a dictionary where key is a tuple and value is the total count 
    #of dogs from that shelter
    #('ABQ Animal Welfare Department', 35.1102, -106.5823): 18

    # Format for the map - moved this code to get_origins()
    #result = [
    #    {"origin": o[0], "latitude": o[1], "longitude": o[2], "count": count}
    #    for o, count in origins.items()
    #]
    print(f"Returning results for map: {origins}")
    return origins
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc:RequestValidationError):
    print("Validation error: ", exc)
    print("Request body received that failed:", await request.body())

    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,content=jsonable_encoder({"detail":exc.errors(),"body":exc.body}),)
#app.include_router(router)

if __name__ == "__main__":
    scrape_and_push()


