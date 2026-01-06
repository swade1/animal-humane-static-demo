import sys

if __name__ == "__main__":
    print("[LOG] generate_weekly_age_group_adoptions_json.py executed", file=sys.stderr)
import json
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
from collections import defaultdict

# Connect to Elasticsearch
es = Elasticsearch("http://localhost:9200")

# Calculate the date 5 weeks ago
now = datetime.now()
five_weeks_ago = now - timedelta(weeks=5)

# Format for week start (Monday)
def week_start(date):
    return (date - timedelta(days=date.weekday())).strftime("%m/%d/%Y")

# Query for adopted dogs in the last 5 weeks
res = es.search(
    index="animal-humane-*",
    body={
        "size": 10000,
        "query": {
            "bool": {
                "must": [
                    {"term": {"status": "adopted"}},
                    {"range": {"adoption_date": {"gte": five_weeks_ago.strftime("%Y-%m-%d")}}}
                ]
            }
        },
        "_source": ["adoption_date", "age_group"]
    }
)

# Group by week and age_group
weekly_counts = defaultdict(lambda: {"Puppy": 0, "Adult": 0, "Senior": 0})
for hit in res["hits"]["hits"]:
    src = hit["_source"]
    adoption_date = src.get("adoption_date")
    age_group = src.get("age_group")
    if adoption_date and age_group:
        try:
            dt = datetime.strptime(adoption_date, "%Y-%m-%d")
            week = week_start(dt)
            if age_group in weekly_counts[week]:
                weekly_counts[week][age_group] += 1
        except Exception:
            continue

# Sort weeks chronologically and get the last 5
sorted_weeks = sorted(weekly_counts.keys(), key=lambda x: datetime.strptime(x, "%m/%d/%Y"))
last_5_weeks = sorted_weeks[-5:]

output_data = []
for week in last_5_weeks:
    entry = {"week": week}
    entry.update(weekly_counts[week])
    output_data.append(entry)

output = {
    "success": True,
    "data": output_data,
    "message": None,
    "error": None
}

with open("react-app/public/api/weekly-age-group-adoptions.json", "w") as f:
    json.dump(output, f, indent=2)
