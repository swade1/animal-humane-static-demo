import json
import os
import subprocess
import sys
from datetime import datetime
from elasticsearch import Elasticsearch


def run_in_container_and_get_urls(container, script):
    result = subprocess.run(["docker", "exec", "-i", container, "python", script], capture_output=True, text=True, timeout=30)
    #print("STDOUT:", repr(result.stdout))  # Shows the exact stdout output
    #print("STDERR:", repr(result.stderr)) 
    if result.returncode != 0:
        print(result.stderr)
        raise Exception(f"Script {script} failed in container {container}.")
    try:
        output = json.loads(result.stdout)
        urls = {
            "adoptions": output.get("adopted_dogs", []),
            "returned": output.get("returned_dogs", []),
            "trial_adoptions": output.get("trial_adoption_dogs", [])
        }
        return urls
    except Exception as e:
        print("Failed to parse output:", e)
        return None

# result is: {'adoptions': [{'name': 'Princess Bubble Gum ', 'dog_id': 212478123, 'url': 'https://new.shelterluv.com/embed/animal/212478123', 'location': ''}], 
def update_adoption(es, adopted_dogs):
    for dog in adopted_dogs:
        dog_id = dog["dog_id"]
        # Find the most recent document for this dog_id
        res = es.search(
            index="animal-humane-*",
            body={
                "query": {"match": {"id": dog_id}},
                "sort":[{"_index":{"order":"desc"}}],
                "size": 1
            }
        )
        hits = res["hits"]["hits"]
        if hits:
            doc = hits[0] 
            es.update(
                index=doc["_index"],
                id=doc["_id"],
                body={"doc": {"status": "adopted", "location":""}}
            )

#'returned': [{'name': 'Snapdragon', 'dog_id': 212533095, 'url': 'https://new.shelterluv.com/embed/animal/212533095', 'location': 'Main Cam    pus - Main Kennel South, MKS-05'}],
def update_return(es, returned_dogs):#

    for dog in returned_dogs:
        dog_id = dog["dog_id"]
        # Find the most recent docs for this dog
        res = es.search(
            index="animal-humane-*",
            body={"query": {"match": {"id": dog_id}}, "sort":[{"_index":{"order":"desc"}}], "size": 2 })
         
        hits = res["hits"]["hits"]

        #Increment just once on the day the dog is returned 
        doc1 = hits[0]["_source"]
        doc2 = hits[1]["_source"]
        date1 = doc1.get("timestamp", "")[:10]  # Adjust field/format as needed
        date2 = doc2.get("timestamp", "")[:10]  # Adjust field/format as needed
        if date1 == date2:
            # Dates are the same, skip update
            continue
        else:
            index = hits[0]["_index"] 
            doc_id = hits[0]["_id"]
            current_returned = doc1.get("returned", 0)
            es.update(
                index=index,
                id=doc_id,
                body={"doc": {"returned": current_returned + 1}}
            )
         
#'trial_adoptions': [{'name': 'Wilbur', 'dog_id': 210495598, 'url': 'https://new.shelterluv.com/embed/animal/210495598', 'location': 'Main Campus, Trial Adoption', 'origin': 'ABQ Animal Welfare Department', 'status': 'Available', 'intake_date': '2026-01-07', 'length_of_stay_days': 2, 'birthdate': '2024-09-18', 'age_group': 'Adult', 'breed': 'Retriever, Labrador', 'secondary_breed': 'Mix', 'weight_grou
def update_trial_adoption(es,trial_dogs):
    for dog in trial_dogs:
        contains_trial_adoption = "Trial Adoption" in dog["location"]
        if contains_trial_adoption:
            pass
        else:
            res = es.search(index="animal-humane-*",body={"query":{"match":{"id":"dog_id"}},"sort":[{"_index":{"order":"desc"}}],"size":1})
            hits = res["hits"]["hits"]
            if hits:
                doc = hits[0]
                es.update(
                    index=doc["_index"],
                    id=doc["_id"],
                    body={"doc": {"location":dog["location"].split(",", 1)[0] + ", Trial Adoption"}}
                )
def run_script(script_name):
    print(f"Running {script_name}...")
    result = subprocess.run([sys.executable, script_name], capture_output=True, text=True)

    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise Exception(f"Script {script_name} failed.")

def git_push():
    #git add all files
    subprocess.run(["git","add","."], check=True)
    commit_message = "Programmatic update to repo after recent run"

    #git commit message
    subprocess.run(["git", "commit", "-m", commit_message], check=True)
   
    #git push origin main
    subprocess.run(["git","push","origin","main"],check=True)


if __name__ == "__main__":
    es = Elasticsearch("http://localhost:9200")

    # 1. Run diff_indices_runner.py inside the api docker container
    result = run_in_container_and_get_urls("animal-humane-api-1", "diff_indices_runner.py")
    print()
    print(f"result is: {result}")
    # 2. Update adoption status and returned field 
    #'returned': [{'name': 'Snapdragon', 'dog_id': 212533095, 'url': 'https://new.shelterluv.com/embed/animal/212533095', 'location': 'Main Campus - Main Kennel South, MKS-05'}], 


    if result.get("adoptions"):
        adoption_fields = [
            {
                "dog_id": dog["dog_id"]
            }
            for dog in result.get("adoptions", [])
        ]    
        print("Adopted dogs")
        print(json.dumps(adoption_fields),end="")

        update_adoption(es, adoption_fields)

    if result.get("returned"):
        returned_fields = [
            {
                "dog_id": dog["dog_id"],
                "location": dog["location"]
            }
            for dog in result.get("returned", [])
        ]
        print()
        print("Dogs that have been returned")
        print(json.dumps(returned_fields),end="")

        update_return(es, returned_fields)

        

    # 3. Execute find_missing_dogs.py
    run_script("find_missing_dogs.py")

    # 4. Run generate_diff_analysis_json.py
    run_script("generate_diff_analysis_json.py")

    # 5. Run generate_recent_pupdates_json.py
    run_script("generate_recent_pupdates_json.py")

    # 6. Run the rest of the generate_*.py scripts
    GENERATE_SCRIPTS = [
        "generate_adoptions_json.py",
        "generate_dog_origins_json.py",
        "generate_insights_json_script.py",
        "generate_live_population_json.py",
        "generate_overview_json.py",
        "generate_weekly_age_group_adoptions_json.py",
        "generate_length_of_stay_json.py",
    ]
    for script in GENERATE_SCRIPTS:
        run_script(script)

    # 7. Push all updates to the repo
    git_push()

    # 8. All data on the site is updated (implement your deployment/restart logic here)
    #print("Step 8: Deploy/restart frontend/backend to update site data (implement logic here)")
    # Example: subprocess.run(["docker-compose", "build", "frontend"])
    #          subprocess.run(["docker-compose", "up", "-d", "frontend"])
