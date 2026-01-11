#run this script from the command line with:
# docker exec -it animal-humane-api-1 python diff_indices_runner.py
from datetime import datetime
import json
import sys

from elasticsearch import Elasticsearch
from shelterdog_tracker.elasticsearch_handler import ElasticsearchHandler
from output_utils import print_dog_groups
from config import config


# run_diffs() collects new, adopted, trial adoption, and unlisted dogs
# and prints the results in a table format
def run_diffs(handler):
    availables = handler.get_current_availables()
    idx = handler.get_most_recent_index()
    print(f"most recent index: {idx}")

    results = handler.get_dog_groups(availables,idx)

    new_dogs = handler.get_new_dogs()

    #add new_dogs to results before printing
    if "new_dogs" not in results:
        results["new_dogs"] = []
    results["new_dogs"].extend(new_dogs.get("new_dogs", []))
    return results

def run_updates(handler, results):
    #pass results to to ElasticsearchHandler class function
    handler.update_dogs(results)


# checks unlisted_other_dogs in results to determine if the dog is just unlisted
# or has been adopted (if adopted, location will be empty). Dogs with empty
# locations are moved to the adopted_dogs list and removed from the other_unlisted_dogs
# list
def check_unlisteds_for_adoptees(results):
    other_unlisted = results.get('other_unlisted_dogs', [])
    adopted_dogs = results.get('adopted_dogs', [])

    # Collect dogs to move
    to_move = []
    for dog in other_unlisted:
        dog_id = dog['dog_id']
        es = Elasticsearch("http://elasticsearch:9200")
        query = {
            "sort": {"_index": {"order": "desc"}},
            "query": {"match": {"id": dog_id}}
        }
        response = es.search(
            index="animal-humane-*",
            body=query,
            size=1
        )
        hits = response.get('hits', {}).get('hits', [])
        if hits:
            doc = hits[0]['_source']
            if doc.get('location', '') == '':
                to_move.append(dog)
            else:
                pass
        else:
            print("No results found")

    # Remove moved dogs from other_unlisted
    results['other_unlisted_dogs'] = [dog for dog in other_unlisted if dog not in to_move]
    # Add moved dogs to adopted_dogs
    results['adopted_dogs'] = adopted_dogs + to_move
    return results

if __name__ == "__main__":
    print(f"Elasticsearch host: {config.elasticsearch.host}")
    today_str = datetime.now().strftime('%m%d%Y')
    today_time = datetime.now().strftime('%Hh%Mm')
    index_name = f"animal-humane-{today_str}-{today_time}"

    handler = ElasticsearchHandler(host=config.elasticsearch.host, index_name=index_name)
    results = run_diffs(handler)
    updated_results = check_unlisteds_for_adoptees(results)
    print_dog_groups(updated_results)

    #answer = input("Please enter 'y' to start updates or 'n' to quit: ").strip().lower()
    #if answer == 'y':
    #    run_updates(handler, updated_results)
    #else:
    #    print("Quitting.")
    #    quit()

    if results is not None:
        run_updates(handler,results)
    else:
        print("No results to update")
