#run this script from the command line with:
# docker exec -it animal-humane-scheduler-1 python diff_indices_runner.py
from datetime import datetime
import json
    
from elasticsearch import Elasticsearch
    
from shelterdog_tracker.elasticsearch_handler import ElasticsearchHandler
from output_utils import print_dog_groups
from config import config

def run_diffs(handler):
    availables = handler.get_current_availables()
    #print(f"availables passed to get_unlisted_dog_groups are: {availables}")
    idx = handler.get_most_recent_index()
    #Verify that unlisted dogs are not in a trial adoption and if they are, change group from unlisted to trial adoption
    #Dogs can be unlisted and then while unlisted, have a location change. This will not be detected since their last 
    #listing will contain their last listed location. Need to navigate to their url and check the location to catch these.
    #Unlisted dogs in foster homes can also be adopted without returning to the website (Zuni, Frederick)
    # Add new group for returned dogs. They will be included in the availables list and can be identified as previously 
    # existing in the data set. if length_of_stay_days == 1, check if their id exists in the data store. if it does, this
    # means they have been gone and have now returned. 

    #get_unlisted_dog_groups also returns returned dogs - might be best to call that function separately for clarity
    results = handler.get_dog_groups(availables, idx)
    #print(f"unlisted dog groups: {results}")

    new_dogs = handler.get_new_dogs()
    
    #add new_dogs to results before printing
    if "new_dogs" not in results:
        results["new_dogs"] = []
    results["new_dogs"].extend(new_dogs.get("new_dogs", []))    
    #print(results)
    print_dog_groups(results)
    return results

def run_updates(handler, results):
    #pass results to to ElasticsearchHandler class function
    handler.update_dogs(results)  

if __name__ == "__main__":
    import sys
    print("[DEBUG] Starting diff_indices_runner.py", file=sys.stderr, flush=True)
    today_str = datetime.now().strftime('%m%d%Y')
    today_time = datetime.now().strftime('%Hh%Mm')
    index_name = f"animal-humane-{today_str}-{today_time}"

    print(f"[DEBUG] Creating ElasticsearchHandler for index: {index_name}", file=sys.stderr, flush=True)
    handler = ElasticsearchHandler(host=config.elasticsearch.host, index_name=index_name)
    print("[DEBUG] Running run_diffs()", file=sys.stderr, flush=True)
    results = run_diffs(handler)
    print("[DEBUG] Finished run_diffs()", file=sys.stderr, flush=True)

    # Optionally run updates automatically or skip
    # print("[DEBUG] Skipping updates step", file=sys.stderr, flush=True)

    # Print results as JSON to stdout for orchestrator
    print("[DEBUG] Printing results as JSON", file=sys.stderr, flush=True)
    print(json.dumps(results), flush=True)
 
    

    

