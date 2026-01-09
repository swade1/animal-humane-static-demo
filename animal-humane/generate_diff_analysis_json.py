import sys

if __name__ == "__main__":
    print("[LOG] generate_diff_analysis_json.py executed", file=sys.stderr)
#!/usr/bin/env python3
"""
Fetches diff analysis data from the backend API and writes it to react-app/public/api/diff-analysis.json for the React frontend.
"""
import requests
import json
import os

# Configurable paths
API_URL = "http://localhost:8000/api/diff-analysis"  # Adjust if needed
OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__), "react-app", "public", "api", "diff-analysis.json"
)

def main():
    response = requests.post("http://localhost:8000/api/cache/clear")
    print(response.status_code, response.text)
    try:
        resp = requests.get(API_URL)
        resp.raise_for_status()
        data = resp.json()
        # Write to file
        with open(OUTPUT_PATH, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Wrote diff analysis data to {OUTPUT_PATH}")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()

response = requests.post("http://localhost:8000/api/cache/clear")
print(response.status_code, response.text)
