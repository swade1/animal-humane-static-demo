#!/usr/bin/env python3
"""
Script to populate Docker Elasticsearch with initial data
"""
from datetime import datetime
from shelterdog_tracker.shelter_scraper import ShelterScraper
from shelterdog_tracker.elasticsearch_handler import ElasticsearchHandler

def main():
    print("🔄 Populating Docker Elasticsearch with initial data")
    print("=" * 55)
    
    try:
        # Create scraper and handler
        scraper = ShelterScraper(main_url="https://animalhumanenm.org/adopt/adoptable-dogs/")
        
        today_str = datetime.now().strftime('%Y%m%d')
        today_time = datetime.now().strftime('%H%M')
        index_name = f"animal-humane-{today_str}-{today_time}"
        
        handler = ElasticsearchHandler(host="http://localhost:9200", index_name=index_name)
        
        print(f"📊 Creating index: {index_name}")
        
        # Create index
        handler.es.indices.create(index=index_name, ignore=400)
        
        print("🌐 Scraping current data from website...")
        
        # Scrape data
        all_dogs = scraper.scrape_all_dogs()
        print(f"📥 Scraped {len(all_dogs)} dogs")
        
        # Push to Elasticsearch
        print("📤 Pushing data to Elasticsearch...")
        handler.push_dogs_to_elasticsearch(all_dogs)
        
        # Update alias
        print("🔗 Updating alias...")
        handler.es.indices.update_aliases(body={
            "actions": [
                {"remove": {"index": "*", "alias": "animal-humane-latest"}},
                {"add": {"index": index_name, "alias": "animal-humane-latest"}},
            ]
        })
        
        print(f"✅ Successfully populated Docker Elasticsearch!")
        print(f"📊 Index: {index_name}")
        print(f"🐕 Dogs: {len(all_dogs)}")
        print("\n🎉 Your FastAPI server should now work properly!")
        
    except Exception as e:
        print(f"❌ Error populating Elasticsearch: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()