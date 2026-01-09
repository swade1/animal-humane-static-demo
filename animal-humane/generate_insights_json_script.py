import os
import json
from elasticsearch import Elasticsearch
from datetime import datetime, timedelta

# Configurable parameters
ES_HOST = os.environ.get("ES_HOST", "localhost")
ES_PORT = int(os.environ.get("ES_PORT", 9200))
ES_USER = os.environ.get("ES_USER")
ES_PASS = os.environ.get("ES_PASS")
INDEX = os.environ.get("ES_INDEX", "animal-humane-*")
DATE_FIELD = "timestamp"  # Use 'timestamp' instead of 'adoption_date'
NAME_FIELD = "name.keyword"
ID_FIELD = "id"
ADOPTED_STATUS = os.environ.get("ADOPTED_STATUS", "adopted")
STATUS_FIELD = os.environ.get("STATUS_FIELD", "status")

if ES_USER and ES_PASS:
    es = Elasticsearch(f"http://{ES_HOST}:{ES_PORT}", http_auth=(ES_USER, ES_PASS))
else:
    es = Elasticsearch(f"http://{ES_HOST}:{ES_PORT}")

query = {
    "size": 0,
    "query": {
        "term": {
            STATUS_FIELD: ADOPTED_STATUS
        }
    },
    "aggs": {
        "adoptions_per_day": {
            "date_histogram": {
                "field": DATE_FIELD,
                "calendar_interval": "day",
                "format": "MM/dd/yyyy",
                "time_zone": "-07:00"
            },
            "aggs": {
                "unique_dogs": {
                    "terms": {
                        "field": ID_FIELD,
                        "size": 10000
                    },
                    "aggs": {
                        "dog_names": {
                            "top_hits": {
                                "_source": ["name"],
                                "size": 1
                            }
                        }
                    }
                }
            }
        }
    }
}

resp = es.search(index=INDEX, body=query)

# Find the full date range
buckets = resp['aggregations']['adoptions_per_day']['buckets']
if buckets:
    min_date = buckets[0]['key_as_string']
    max_date = buckets[-1]['key_as_string']
else:
    min_date = max_date = None

# Build a dict for fast lookup
bucket_map = {b['key_as_string']: b for b in buckets}

# Generate all dates in the range
results = []
if min_date and max_date:
    cur_date = datetime.strptime(min_date, "%m/%d/%Y")
    end_date = datetime.strptime(max_date, "%m/%d/%Y")
    while cur_date <= end_date:
        date_str = cur_date.strftime("%m/%d/%Y")
        bucket = bucket_map.get(date_str)
        if bucket:
            unique_dogs = bucket['unique_dogs']['buckets']
            names = []
            for dog in unique_dogs:
                hits = dog['dog_names']['hits']['hits']
                if hits:
                    name = hits[0]['_source'].get('name')
                    if name:
                        names.append(name)
            count = len(names)
        else:
            names = []
            count = 0
        results.append({
            "date": date_str,
            "count": count,
            "names": names
        })
        cur_date += timedelta(days=1)

output = {
    "success": True,
    "data": {
        "dailyAdoptions": results
    },
    "message": None,
    "error": None
}

# Write output to file
output_path = os.path.join(os.path.dirname(__file__), './react-app/public/api/insights.json')
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2)

print(f"Wrote output to {output_path}")
