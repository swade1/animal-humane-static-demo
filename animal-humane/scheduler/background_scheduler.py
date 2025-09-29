#!/usr/bin/env python3
"""
Background scheduler that runs independently of the main API
Can be deployed to a cloud service or run as a system service
"""
import schedule
import time
import logging
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from shelterdog_tracker.shelter_scraper import ShelterScraper
from shelterdog_tracker.elasticsearch_handler import ElasticsearchHandler
from scheduler.diff_analyzer import DiffAnalyzer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AnimalHumaneScheduler:
    def __init__(self):
        self.scraper = ShelterScraper(main_url="https://animalhumanenm.org/adopt/adoptable-dogs/")
        self.diff_analyzer = DiffAnalyzer()
        # Get Elasticsearch host from environment variable for Docker
        self.es_host = os.getenv('ELASTICSEARCH_HOST', 'http://localhost:9200')
        
    def scrape_and_index(self):
        """Scrape current data and push to Elasticsearch"""
        try:
            logger.info("Starting scheduled scrape and index operation")
            
            today_str = datetime.now().strftime('%Y%m%d')
            today_time = datetime.now().strftime('%H%M')
            index_name = f"animal-humane-{today_str}-{today_time}"
            
            handler = ElasticsearchHandler(host=self.es_host, index_name=index_name)
            
            # Create index
            handler.es.indices.create(index=index_name, ignore=400)
            logger.info(f"Created index: {index_name}")
            
            # Scrape data
            all_dogs = self.scraper.scrape_all_dogs()
            logger.info(f"Scraped {len(all_dogs)} dogs")
            
            # Push to Elasticsearch
            handler.push_dogs_to_elasticsearch(all_dogs)
            logger.info(f"Pushed {len(all_dogs)} dogs to Elasticsearch")
            
            # Update alias
            handler.es.indices.update_aliases(body={
                "actions": [
                    {"remove": {"index": "*", "alias": "animal-humane-latest"}},
                    {"add": {"index": index_name, "alias": "animal-humane-latest"}},
                ]
            })
            logger.info(f"Updated alias to point to {index_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in scrape_and_index: {e}", exc_info=True)
            return False
    
    def run_diff_analysis(self):
        """Run difference analysis and save results to file"""
        try:
            logger.info("Starting diff analysis")
            
            # Run the analysis
            results = self.diff_analyzer.analyze_differences()
            
            if results:
                logger.info(f"Diff analysis completed. Found {len(results.get('changes', []))} changes")
                return True
            else:
                logger.warning("Diff analysis returned no results")
                return False
                
        except Exception as e:
            logger.error(f"Error in diff analysis: {e}", exc_info=True)
            return False
    
    def health_check(self):
        """Check if Elasticsearch is accessible"""
        try:
            handler = ElasticsearchHandler(host=self.es_host, index_name="animal-humane-latest")
            handler.es.ping()
            logger.info("Health check passed - Elasticsearch is accessible")
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

def main():
    logger.info("Starting Animal Humane Background Scheduler")
    
    scheduler = AnimalHumaneScheduler()
    
    # Schedule jobs - Mountain Time (UTC-7 in summer, UTC-6 in winter)
    # Note: These times are in the container's timezone (UTC by default)
    # We'll set the container timezone to Mountain Time in docker-compose
    
    # Scrape at: 9am, 11am, 1pm, 3pm, 5pm, 7pm Mountain Time
    schedule.every().day.at("09:00").do(scheduler.scrape_and_index)  # 9 AM MT
    schedule.every().day.at("11:00").do(scheduler.scrape_and_index)  # 11 AM MT
    schedule.every().day.at("13:00").do(scheduler.scrape_and_index)  # 1 PM MT
    schedule.every().day.at("15:00").do(scheduler.scrape_and_index)  # 3 PM MT
    schedule.every().day.at("17:00").do(scheduler.scrape_and_index)  # 5 PM MT
    schedule.every().day.at("19:00").do(scheduler.scrape_and_index)  # 7 PM MT
    
    # Run diff analysis 5 minutes after each scrape
    schedule.every().day.at("09:05").do(scheduler.run_diff_analysis)  # 9:05 AM MT
    schedule.every().day.at("11:05").do(scheduler.run_diff_analysis)  # 11:05 AM MT
    schedule.every().day.at("13:05").do(scheduler.run_diff_analysis)  # 1:05 PM MT
    schedule.every().day.at("15:05").do(scheduler.run_diff_analysis)  # 3:05 PM MT
    schedule.every().day.at("17:05").do(scheduler.run_diff_analysis)  # 5:05 PM MT
    schedule.every().day.at("19:05").do(scheduler.run_diff_analysis)  # 7:05 PM MT
    
    # Health check every hour
    schedule.every().hour.do(scheduler.health_check)
    
    logger.info("Scheduler configured with the following jobs (Mountain Time):")
    logger.info("- Scraping: 9:00, 11:00, 13:00, 15:00, 17:00, 19:00")
    logger.info("- Diff analysis: 9:05, 11:05, 13:05, 15:05, 17:05, 19:05")
    logger.info("- Health check: Every hour")
    
    # Run initial health check
    if not scheduler.health_check():
        logger.error("Initial health check failed. Please ensure Elasticsearch is running.")
        sys.exit(1)
    
    # Log current time and next scheduled jobs
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")
    logger.info(f"Current time: {current_time}")
    
    # Show next few scheduled jobs
    jobs = schedule.get_jobs()
    if jobs:
        logger.info("Next scheduled jobs:")
        for job in sorted(jobs, key=lambda x: x.next_run)[:3]:
            logger.info(f"  - {job.job_func.__name__} at {job.next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Main loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {e}", exc_info=True)

if __name__ == "__main__":
    main()