from datetime import datetime
import subprocess

from shelterdog_tracker.shelter_scraper import ShelterScraper
from shelterdog_tracker.elasticsearch_handler import ElasticsearchHandler

#from shelterdog_tracker.dog_status_updater import DogStatusUpdater
#from diff_indices_runner import run_diffs

def main():
    today_str = datetime.now().strftime('%Y%m%d')
    today_time = datetime.now().strftime('%H%M') 

    scraper = ShelterScraper(main_url="https://animalhumanenm.org/adopt/adoptable-dogs/")
  
    index_name = f"animal-humane-{today_str}-{today_time}"

    handler = ElasticsearchHandler(host="http://localhost:9200", index_name=index_name)

    handler.es.indices.create(index=index_name)

    all_dogs = scraper.scrape_all_dogs()

    handler.push_dogs_to_elasticsearch(all_dogs)
 
    subprocess.run(["python3","diff_indices_runner.py"])

    return    


if __name__ == "__main__":
    main()
