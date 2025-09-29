import csv
from elasticsearch import Elasticsearch

# -------------------------------
# Settings
# -------------------------------
CSV_FILE = "Absent_Unknowns_sorted.csv"  # <-- path to your CSV file
ES_HOST = "http://localhost:9200"
NEW_ORIGIN = None  # This will come from the CSV row

# Connect to Elasticsearch
es = Elasticsearch(ES_HOST)

# -------------------------------
# Function to update origin field
# -------------------------------
def update_origin(index_name, dog_id, new_origin_value):
    """
    Finds all docs in 'index_name' with id.keyword == dog_id and
    adds/updates 'origin' if missing, empty, or 'Unknown'.
    """
    query = {
        "script": {
            "source": """
                if (ctx._source.origin == null || 
                    ctx._source.origin == "" || 
                    ctx._source.origin == "Unknown") {
                    ctx._source.origin = params.new_origin;
                }
            """,
            "lang": "painless",
            "params": {
                "new_origin": new_origin_value
            }
        },
        "query": {
            "term": {
                "id": dog_id
            }
        }
    }

    resp = es.update_by_query(index=index_name, body=query, conflicts="proceed", refresh=True)
    print(f"Updated docs in {index_name} for id={dog_id}: {resp.get('updated', 0)} updated")

# -------------------------------
# Read CSV and process rows
# -------------------------------
with open(CSV_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    reader.fieldnames = [name.strip() for name in reader.fieldnames]  # strip spaces
    for row in reader:
        index_name = row["index"].strip()
        dog_id = row["id"].strip()
        origin_value = row["origin"].strip() if row.get("origin") else ""

        # Only proceed if the row has an index, ID, and a non-empty origin value in CSV
        if index_name and dog_id and origin_value:
            update_origin(index_name, dog_id, origin_value)

