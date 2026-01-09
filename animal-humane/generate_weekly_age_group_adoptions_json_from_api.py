#!/usr/bin/env python3
"""
Fetches weekly age group adoptions data from the backend API and writes it to react-app/public/api/weekly-age-group-adoptions.json for the React frontend.
"""
import requests
import json
import os

# Configurable paths
API_URL = "http://localhost:8000/api/weekly-age-group-adoptions"  # Adjust if needed
OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__), "react-app", "public", "api", "weekly-age-group-adoptions.json"
)

def main():
    try:
        resp = requests.get(API_URL)
        resp.raise_for_status()
        data = resp.json()
        # Write to file
        with open(OUTPUT_PATH, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Wrote weekly age group adoptions data to {OUTPUT_PATH}")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
