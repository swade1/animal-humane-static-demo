import sys

if __name__ == "__main__":
    print("[LOG] generate_recent_pupdates_json.py executed", file=sys.stderr)

#!/usr/bin/env python3
"""
Aggregates recent pupdates data from diff-analysis.json and missing_dogs.txt, and writes to react-app/public/api/recent-pupdates.json for the React frontend.
"""
import json
import os

BASE_DIR = os.path.dirname(__file__)
DIFF_ANALYSIS_PATH = os.path.join(BASE_DIR, "react-app", "public", "api", "diff-analysis.json")
MISSING_DOGS_PATH = os.path.join(BASE_DIR, "react-app", "public", "missing_dogs.txt")
OUTPUT_PATH = os.path.join(BASE_DIR, "react-app", "public", "api", "recent-pupdates.json")

def load_diff_analysis():
    print("load_diff_analysis() has been called")
    with open(DIFF_ANALYSIS_PATH, "r") as f:
        return json.load(f)["data"]

def load_missing_dogs():
    dogs = []
    if not os.path.exists(MISSING_DOGS_PATH):
        return dogs
    with open(MISSING_DOGS_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("Missing dogs"):
                continue
            if ":" in line:
                dog_id, name = line.split(":", 1)
                dogs.append({
                    "id": int(dog_id.strip()),
                    "name": name.strip(),
                    "url": f"https://new.shelterluv.com/embed/animal/{dog_id.strip()}",
                    "status": None,
                    "location": None,
                    "section_metadata": {"source": "missing_dogs"}
                })
    return dogs

def map_diff_dogs(dogs, section):
    # section: e.g. "new", "returned", "adopted", "trial", "unlisted"
    mapped = []
    for d in dogs:
        mapped.append({
            "id": d.get("dog_id") or d.get("id"),
            "name": d.get("name"),
            "url": d.get("url"),
            "status": d.get("status"),
            "location": d.get("location"),
            "section_metadata": {"source": f"diff_analysis_{section}"}
        })
    return mapped

def main():
    try:
        diff = load_diff_analysis()
        print(f"diff returned is: {diff}")
        missing = load_missing_dogs()

        result = {
            "success": True,
            "data": {
                "new_dogs": map_diff_dogs(diff.get("new_dogs", []), "new"),
                "returned_dogs": map_diff_dogs(diff.get("returned_dogs", []), "returned"),
                "adopted_dogs": map_diff_dogs(diff.get("adopted_dogs", []), "adopted"),
                "trial_dogs": map_diff_dogs(diff.get("trial_adoption_dogs", []), "trial"),
                "unlisted_dogs": map_diff_dogs(diff.get("other_unlisted_dogs", []), "unlisted"),
                "available_soon": missing
            },
            "message": None,
            "error": None
        }

        # Optionally add section_configs, total_dogs, etc. if needed
        result["data"]["total_dogs"] = sum(len(result["data"][k]) for k in [
            "new_dogs", "returned_dogs", "adopted_dogs", "trial_dogs", "unlisted_dogs", "available_soon"
        ])

        with open(OUTPUT_PATH, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Wrote recent pupdates data to {OUTPUT_PATH}")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
