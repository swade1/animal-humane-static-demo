#!/usr/bin/env python3
"""
Test script to check live status parsing
"""
import requests
import re
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent))

from scheduler.diff_analyzer import DiffAnalyzer

def test_live_status():
    analyzer = DiffAnalyzer()
    
    # Test the three dogs in question
    test_dogs = [
        ("Gnocchi", "211823717"),
        ("Havana", "211903456"), 
        ("Tim", "211808307")
    ]
    
    for name, dog_id in test_dogs:
        print(f"\n=== Testing {name} (ID: {dog_id}) ===")
        status = analyzer.check_live_status(dog_id)
        print(f"Location: '{status['location']}'")
        print(f"Is adopted: {status['is_adopted']}")
        print(f"Is trial adoption: {status['is_trial_adoption']}")
        
        # Also test direct URL access
        url = f"https://new.shelterluv.com/embed/animal/{dog_id}"
        try:
            response = requests.get(url, timeout=10)
            print(f"HTTP Status: {response.status_code}")
            
            content = response.text
            
            # Look for any mention of location, trial, adoption, etc.
            keywords = ['location', 'trial', 'adoption', 'campus', 'available', 'adopted']
            
            print("=== Content Analysis ===")
            lines = content.split('\n')
            for i, line in enumerate(lines):
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in keywords):
                    # Print surrounding context
                    start = max(0, i-2)
                    end = min(len(lines), i+3)
                    print(f"Lines {start}-{end}:")
                    for j in range(start, end):
                        marker = ">>> " if j == i else "    "
                        print(f"{marker}{j}: {lines[j].strip()}")
                    print()
                    
        except Exception as e:
            print(f"Error accessing URL: {e}")

if __name__ == "__main__":
    test_live_status()