from datetime import datetime
import subprocess

from shelterdog_tracker.shelter_scraper import ShelterScraper
from shelterdog_tracker.elasticsearch_handler import ElasticsearchHandler
from utils.logger import setup_logger

#from shelterdog_tracker.dog_status_updater import DogStatusUpdater
#from diff_indices_runner import run_diffs

logger = setup_logger("main_application")

def main():
    logger.info("Starting main application startup sequence")

    today_str = datetime.now().strftime('%Y%m%d')
    today_time = datetime.now().strftime('%H%M')
    index_name = f"animal-humane-{today_str}-{today_time}"
    logger.info("Prepared index name %s", index_name)

    scraper = ShelterScraper(main_url="https://animalhumanenm.org/adopt/adoptable-dogs/")
    logger.info("Initialized shelter scraper for %s", scraper.main_url)

    handler = ElasticsearchHandler(host="http://elasticsearch:9200", index_name=index_name)
    logger.info("Connected to Elasticsearch at %s", handler.host)

    try:
        logger.info("Creating index %s", index_name)
        handler.es.indices.create(index=index_name)
        logger.info("Index %s created", index_name)

        logger.info("Scraping available dogs")
        all_dogs = scraper.scrape_all_dogs()
        logger.info("Scraping complete, collected %d dogs", len(all_dogs))

        logger.info("Pushing dogs to Elasticsearch index %s", index_name)
        handler.push_dogs_to_elasticsearch(all_dogs)
        logger.info("Push to Elasticsearch completed")

        logger.info("Running diff_indices_runner.py")
        result = subprocess.run(
            ["python3", "diff_indices_runner.py"],
            check=True,
            capture_output=True,
            text=True,
        )
        if result.stdout:
            logger.info("diff_indices_runner.py output:\n%s", result.stdout.strip())
        if result.stderr:
            logger.warning("diff_indices_runner.py errors:\n%s", result.stderr.strip())

    except Exception as exc:
        logger.exception("Main application startup sequence failed: %s", exc)
        raise

    logger.info("Main application startup sequence completed successfully")


if __name__ == "__main__":
    main()
