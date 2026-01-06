import sys

if __name__ == "__main__":
    print("[LOG] generate_length_of_stay_json.py executed", file=sys.stderr)

import json
from elasticsearch import Elasticsearch
from collections import defaultdict
from datetime import datetime

# Connect to Elasticsearch
es = Elasticsearch("http://localhost:9200")

# Get all unique dog IDs
ids = es.search(index="animal-humane-*",body={"size": 0,"aggs": {"unique_ids": {"terms": {"field": "id", "size": 10000}}}})

dog_ids = [bucket["key"] for bucket in ids["aggregations"]["unique_ids"]["buckets"]]

# Define bins
bins = [
    (0, 30), (31, 60), (61, 90), (91, 120), (121, 150),
    (151, 180), (181, 210), (211, 240), (241, 270), (271, 300)
]

binned_dogs = defaultdict(list)

for dog_id in dog_ids:
    # Get the most recent document for this dog
    res = es.search(
        index="animal-humane-*",
        body={
            "size": 1,
            "query": {"term": {"id": dog_id}},
            "sort": [{"timestamp": {"order": "desc"}}]
        }
    )
    if res["hits"]["hits"]:
        doc = res["hits"]["hits"][0]["_source"]
        if doc.get("status") == "Available":
            intake_date_str = doc.get("intake_date")
            losd = 0
            if intake_date_str:
                try:
                    intake_date = datetime.strptime(intake_date_str, "%Y-%m-%d")
                    today = datetime.now()
                    losd = (today - intake_date).days
                except Exception:
                    losd = 0
            # Find the bin
            for b_start, b_end in bins:
                if b_start <= losd <= b_end:
                    binned_dogs[(b_start, b_end)].append({
                        "name": doc.get("name"),
                        "breed": doc.get("breed"),
                        "age_group": doc.get("age_group"),
                        "length_of_stay_days": losd
                    })
                    break
output = {
    "success": True,
    "data": {
        "bins": []
    }
}

for b_start, b_end in bins:
    dogs = binned_dogs[(b_start, b_end)]
    output["data"]["bins"].append({
        "min": b_start,
        "max": b_end,
        "count": len(dogs),
        "dogs": dogs
    })

with open("react-app/public/api/length-of-stay.json", "w") as f:
    json.dump(output, f, indent=2)
