#!/usr/bin/env python3
"""
Test script to verify scraping works
"""
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent))

from shelterdog_tracker.shelter_scraper import ShelterScraper

def test_scraping():
    scraper = ShelterScraper(main_url="https://animalhumanenm.org/adopt/adoptable-dogs/")
    
    print("Testing scraper...")
    try:
        # Test URL fetching
        urls = scraper.fetch_iframe_urls()
        print(f"Found {len(urls)} URLs:")
        for url in urls:
            print(f"  - {url}")
        
        if urls:
            # Test scraping from first URL
            print(f"\nTesting scraping from first URL: {urls[0]}")
            dogs = scraper.scrape_dogs_from_urls([urls[0]])
            print(f"Scraped {len(dogs)} dogs from first URL")
            
            if dogs:
                print("Sample dog:")
                sample_dog = dogs[0]
                print(f"  Name: {sample_dog.name}")
                print(f"  ID: {sample_dog.id}")
                print(f"  Status: {sample_dog.status}")
                print(f"  Location: {sample_dog.location}")
        else:
            print("No URLs found - scraping will fail")
            
    except Exception as e:
        print(f"Scraping test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scraping()