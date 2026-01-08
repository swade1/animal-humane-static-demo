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
ten_weeks_ago = now - timedelta(weeks=10)

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
                    {"term": {"status": "adopted"}}
                    #{"range": {"adoption_date": {"gte": ten_weeks_ago.strftime("%Y-%m-%d")}}}
                ]
            }
        },
        "_source": ["timestamp", "age_group"]
    }
)
#print(f"res: {res}")
# Group by week and age_group
weekly_counts = defaultdict(lambda: {"Puppy": 0, "Adult": 0, "Senior": 0})
#print(f"weekly_counts: {weekly_counts}")
for hit in res["hits"]["hits"]:
    src = hit["_source"]
    adoption_date = src.get("timestamp")
    date_str = adoption_date[:10]  # Extract 'YYYY-MM-DD'
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    #print(dt)
    age_group = src.get("age_group")
    if adoption_date and age_group:
        try:
            week = week_start(dt)
            #print(f"week: {week}")
            if age_group in weekly_counts[week]:
                weekly_counts[week][age_group] += 1
        except Exception:
            continue

# Sort weeks chronologically and get the last 5
sorted_weeks = sorted(weekly_counts.keys(), key=lambda x: datetime.strptime(x, "%m/%d/%Y"))
#print(f"sorted_weeks: {sorted_weeks}")
last_10_weeks = sorted_weeks[-10:]
#print(f"last_10_weeks: {last_10_weeks}")

output_data = []
for week in last_10_weeks:
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
