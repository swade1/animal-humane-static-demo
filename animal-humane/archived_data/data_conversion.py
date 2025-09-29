import json

# Input and output filenames
input_filename = "animal-humane-07162025-15h14m.json"
output_filename = "animal-humane-07162025-15h14m.ndjson"

# STEP 1: Read the JSON objects from your file.
# If your input is a JSON array:  [ {...}, {...}, ... ]
# Or, if it's a sequence of JSON objects separated by commas (not wrapped in [])
# In that case, fix the file or parse it line by line.

# --- IF your input file is a JSON array:
with open(input_filename, "r", encoding="utf-8") as f:
    docs = json.load(f)

# --- IF your input file is not a valid JSON array, but many JSON objects separated by commas (not wrapped in []):
# Fix your file by putting [ at the top and ] at the bottom, or
# Use:
# with open(input_filename, "r", encoding="utf-8") as f:
#     text = f.read()
#     text = "[" + text.strip().rstrip(",") + "]"
#     docs = json.loads(text)

# STEP 2: Write them out in bulk NDJSON format
with open(output_filename, "w", encoding="utf-8") as f:
    for doc in docs:
        # Build action/meta line
        action = {
            "index": {
                "_index": doc["_index"],
                "_id": doc["_id"]
            }
        }
        f.write(json.dumps(action) + "\n")

        # Build document line
        src = doc["_source"]
        # Convert "locations": [locstr] -> "location": locstr (string)
        loc_list = src.get("locations", [])
        if isinstance(loc_list, list):
            location = loc_list[0] if loc_list else ""
        else:
            location = loc_list  # already str
        # Copy all fields except locations, and use location instead
        out_doc = {k: v for k, v in src.items() if k != "locations"}
        out_doc["location"] = location
        f.write(json.dumps(out_doc) + "\n")

print(f"Converted {len(docs)} docs to Elasticsearch bulk NDJSON.")

