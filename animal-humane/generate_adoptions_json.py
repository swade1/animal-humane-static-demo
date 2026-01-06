import sys

if __name__ == "__main__":
    print("[LOG] generate_adoptions_json.py executed", file=sys.stderr)
#!/usr/bin/env python3
"""
Fetches adoptions from the /api/adoptions endpoint and writes them to react-app/public/api/adoptions.json.
Copies the API output directly to the static file.
"""

import requests
import json
import os

# Configurable paths
API_URL = "http://localhost:8000/api/adoptions"  # Adjust if running elsewhere
OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__), "react-app", "public", "api", "adoptions.json"
)

def main():
    try:
        resp = requests.get(API_URL)
        resp.raise_for_status()
        data = resp.json()
        # Write the API output directly to the static file
        with open(OUTPUT_PATH, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Wrote adoptions API output to {OUTPUT_PATH}")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
