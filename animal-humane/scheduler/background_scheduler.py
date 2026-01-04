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
from concurrent.futures import ThreadPoolExecutor

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
        # Thread pool executor for running long tasks asynchronously
        self.executor = ThreadPoolExecutor(max_workers=4)
        # Get Elasticsearch host from environment variable for Docker
        self.es_host = os.getenv('ELASTICSEARCH_HOST', 'http://localhost:9200')
        
    def run_async(self, fn, *args, **kwargs):
        """Submit a task to the executor so scheduled jobs don't block the scheduler loop"""
        try:
            self.executor.submit(fn, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error submitting task to executor: {e}")

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
            
            # Update demo site timestamp after successful ingest - DISABLED for manual control
            # self._update_demo_timestamp(index_name)
            
            return True
            
        except Exception as e:
            logger.error(f"Error in scrape_and_index: {e}", exc_info=True)
            return False
    
    def _update_demo_timestamp(self, index_name):
        """Update demo site timestamp after successful data ingest"""
        try:
            import subprocess
            import os
            
            logger.info(f"Updating demo timestamp for index: {index_name}")
            
            # Run the timestamp update script
            script_path = os.path.join(os.path.dirname(__file__), '..', 'update_static_data.py')
            result = subprocess.run(['python', script_path], 
                                  capture_output=True, text=True, cwd=os.path.dirname(script_path))
            
            if result.returncode == 0:
                logger.info("✅ Demo timestamp updated successfully")
                
                # Configure git and commit/push changes
                repo_dir = os.path.dirname(script_path)
                
                # Set git config first
                git_config_commands = [
                    ['git', 'config', 'user.name', 'Animal Humane Scheduler'],
                    ['git', 'config', 'user.email', 'scheduler@animalhumane.local'],
                ]
                
                for cmd in git_config_commands:
                    subprocess.run(cmd, cwd=repo_dir, capture_output=True)
                
                # Git commit and push the changes
                git_commands = [
                    ['git', 'add', 'react-app/public/api/last-updated.json'],
                    ['git', 'commit', '-m', f'Auto-update demo timestamp from scheduler - {index_name}'],
                    ['git', 'push', 'origin', 'main']
                ]
                
                for cmd in git_commands:
                    git_result = subprocess.run(cmd, capture_output=True, text=True, cwd=repo_dir)
                    if git_result.returncode != 0:
                        logger.error(f"Git command failed: {' '.join(cmd)}")
                        logger.error(f"Error: {git_result.stderr}")
                        logger.error(f"Output: {git_result.stdout}")
                        return False
                
                logger.info("✅ Demo timestamp changes pushed to GitHub - Vercel will auto-deploy")
                return True
            else:
                logger.error(f"❌ Demo timestamp update failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating demo timestamp: {e}")
            return False

    def run_diff_analysis(self):
        """Run difference analysis and save results to file, update Diff Analysis tab data, and warm up API cache"""
        try:
            logger.info("Starting diff analysis")

            # Clear API cache before running analysis
            try:
                import requests
                api_base = "http://api:8000"  # Adjust if needed
                clear_url = f"{api_base}/api/cache/clear"
                resp = requests.post(clear_url, timeout=15)
                if resp.status_code == 200:
                    logger.info("✅ API cache cleared successfully before diff analysis.")
                else:
                    logger.warning(f"Failed to clear API cache: HTTP {resp.status_code} - {resp.text}")
            except Exception as e:
                logger.error(f"Error clearing API cache: {e}")

            # Run the analysis
            results = self.diff_analyzer.analyze_differences()

            if results:
                logger.info(f"Diff analysis completed. Found {len(results.get('changes', []))} changes")
                
                # Also update the Diff Analysis tab data by calling the ElasticsearchService method
                # This ensures the tab shows the latest categorized dog data
                try:
                    from services.elasticsearch_service import ElasticsearchService
                    es_service = ElasticsearchService()
                    
                    # Run get_diff_analysis in a synchronous context (since we're in a sync method)
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    diff_data = loop.run_until_complete(es_service.get_diff_analysis())
                    loop.close()
                    
                    logger.info(f"Diff Analysis tab data updated: {len(diff_data.get('new_dogs', []))} new, {len(diff_data.get('adopted_dogs', []))} adopted, {len(diff_data.get('trial_adoption_dogs', []))} trial, {len(diff_data.get('other_unlisted_dogs', []))} unlisted")
                    
                except Exception as e:
                    logger.error(f"Error updating Diff Analysis tab data: {e}")
                
                # Update missing dogs list
                self.update_missing_dogs_list()

                # Run the adoptions JSON generator script (disabled; frontend does not use adoptions.json)
                # try:
                #     import subprocess
                #     import os
                #     script_path = os.path.join(os.path.dirname(__file__), '..', 'generate_adoptions_json.py')
                #     result = subprocess.run(['python', script_path], capture_output=True, text=True, cwd=os.path.dirname(script_path))
                #     if result.returncode == 0:
                #         logger.info("✅ Adoptions JSON file updated successfully.")
                #         logger.info(result.stdout)
                #     else:
                #         logger.error(f"❌ Failed to update adoptions JSON file: {result.stderr}")
                # except Exception as e:
                #     logger.error(f"❌ Error running generate_adoptions_json.py: {e}")

                # Warm up the API cache with fresh data
                self._warm_up_api_cache()

                return True
            else:
                logger.warning("Diff analysis returned no results")
                return False
                
        except Exception as e:
            logger.error(f"Error in diff analysis: {e}", exc_info=True)
            return False
    
    def _warm_up_api_cache(self):
        """Warm up the API cache by making requests to all cached endpoints"""
        try:
            logger.info("Warming up API cache with fresh data")
            
            import requests
            
            # API base URL (assuming it's running on the same host)
            api_base = "http://api:8000"  # Adjust if needed
            
            # Endpoints to warm up
            endpoints = [
                "/api/overview",
                "/api/live_population", 
                "/api/insights",
                "/api/diff-analysis",
                "/api/weekly-age-group-adoptions",
                "/api/dog-origins",
                "/api/missing-dogs"
            ]
            
            for endpoint in endpoints:
                try:
                    url = f"{api_base}{endpoint}"
                    logger.debug(f"Warming cache for {endpoint}")
                    response = requests.get(url, timeout=30)
                    
                    if response.status_code == 200:
                        logger.debug(f"Successfully warmed cache for {endpoint}")
                    else:
                        logger.warning(f"Failed to warm cache for {endpoint}: HTTP {response.status_code}")
                        
                except requests.exceptions.RequestException as e:
                    logger.error(f"Error warming cache for {endpoint}: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error warming cache for {endpoint}: {e}")
            
            logger.info("API cache warm-up completed")
            
        except Exception as e:
            logger.error(f"Error in cache warm-up: {e}")
    
    def update_missing_dogs_list(self):
        """Update the missing dogs list by running the find_missing_dogs.py script"""
        try:
            logger.info("Updating missing dogs list")
            
            import subprocess
            import shutil
            
            # Path to the find_missing_dogs.py script
            script_path = os.path.join(os.path.dirname(__file__), '..', 'find_missing_dogs.py')
            
            # Run the script
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(script_path)
            )
            
            if result.returncode == 0:
                logger.info("Missing dogs list updated successfully")
                # Parse the output to get the count
                for line in result.stdout.split('\n'):
                    if 'Found' in line and 'dogs that exist in the file but not in Elasticsearch' in line:
                        logger.info(line.strip())
                        break
                
                # Copy the updated file to the React app's public directory
                source_file = os.path.join(os.path.dirname(script_path), 'missing_dogs.txt')
                react_public_dir = os.path.join(os.path.dirname(__file__), '..', 'react-app', 'public')
                dest_file = os.path.join(react_public_dir, 'missing_dogs.txt')
                
                if os.path.exists(source_file):
                    shutil.copy2(source_file, dest_file)
                    logger.info(f"Copied missing_dogs.txt to React app public directory: {dest_file}")

                    # Call the API to refresh its cache for missing_dogs (internal endpoint)
                    try:
                        import requests
                        api_base = "http://api:8000"
                        refresh_url = f"{api_base}/api/cache/refresh"
                        headers = {}
                        token = os.getenv('INTERNAL_API_TOKEN')
                        if token:
                            headers['X-Internal-Token'] = token

                        resp = requests.post(refresh_url, params={"key": "missing_dogs"}, headers=headers, timeout=15)
                        if resp.status_code == 200:
                            logger.info("Successfully refreshed missing_dogs cache via API")
                        else:
                            logger.warning(f"Failed to refresh missing_dogs cache: HTTP {resp.status_code} - {resp.text}")
                    except Exception as e:
                        logger.error(f"Error calling cache refresh endpoint: {e}")

                else:
                    logger.warning(f"Source file not found: {source_file}")
                    
            else:
                logger.error(f"Failed to update missing dogs list. Return code: {result.returncode}")
                logger.error(f"Stdout: {result.stdout}")
                logger.error(f"Stderr: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Error updating missing dogs list: {e}", exc_info=True)
    
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

import signal

def _parse_index_datetime(index_name: str):
    """Parse index name like animal-humane-YYYYMMDD-HHMM into a datetime or return None"""
    import re
    m = re.search(r"animal-humane-(\d{8})-(\d{4})", index_name)
    if not m:
        return None
    date_part, time_part = m.groups()
    try:
        return datetime.strptime(f"{date_part}{time_part}", "%Y%m%d%H%M")
    except Exception:
        return None


def main():
    logger.info("Starting Animal Humane Background Scheduler")
    
    scheduler = AnimalHumaneScheduler()
    
    # Schedule jobs - Mountain Time (UTC-7 in summer, UTC-6 in winter)
    # Note: These times are in the container's timezone (UTC by default)
    # We'll set the container timezone to Mountain Time in docker-compose
    
    # Scrape at: 9am, 11am, 1pm, 3pm, 5pm, 7pm Mountain Time
    schedule.every().day.at("09:00").do(scheduler.run_async, scheduler.scrape_and_index)  # 9 AM MT
    schedule.every().day.at("11:00").do(scheduler.run_async, scheduler.scrape_and_index)  # 11 AM MT
    schedule.every().day.at("13:00").do(scheduler.run_async, scheduler.scrape_and_index)  # 1 PM MT
    schedule.every().day.at("15:00").do(scheduler.run_async, scheduler.scrape_and_index)  # 3 PM MT
    schedule.every().day.at("17:00").do(scheduler.run_async, scheduler.scrape_and_index)  # 5 PM MT
    schedule.every().day.at("19:00").do(scheduler.run_async, scheduler.scrape_and_index)  # 7 PM MT
    
    # Run diff analysis 10 minutes after each scrape
    schedule.every().day.at("09:05").do(scheduler.run_async, scheduler.run_diff_analysis)  # 9:05 AM MT
    schedule.every().day.at("11:05").do(scheduler.run_async, scheduler.run_diff_analysis)  # 11:05 AM MT
    schedule.every().day.at("13:05").do(scheduler.run_async, scheduler.run_diff_analysis)  # 1:05 PM MT
    schedule.every().day.at("15:05").do(scheduler.run_async, scheduler.run_diff_analysis)  # 3:05 PM MT
    schedule.every().day.at("17:05").do(scheduler.run_async, scheduler.run_diff_analysis)  # 5:05 PM MT
    schedule.every().day.at("19:05").do(scheduler.run_async, scheduler.run_diff_analysis)  # 7:05 PM MT
    
    # Health check every hour
    schedule.every().hour.do(scheduler.run_async, scheduler.health_check)  
    
    logger.info("Scheduler configured with the following jobs (Mountain Time):")
    logger.info("- Scraping: 9:00, 11:00, 13:00, 15:00, 17:00, 19:00")
    logger.info("- Diff analysis: 9:10, 11:10, 13:10, 15:10, 17:10, 19:10")
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

    # Catch up missed scrapes if any (use alias to determine last successful scrape)
    try:
        from elasticsearch import Elasticsearch
        handler = ElasticsearchHandler(host=scheduler.es_host, index_name="animal-humane-latest")
        alias_info = handler.es.indices.get_alias(name="animal-humane-latest", ignore=[404])
        last_index_time = None
        if alias_info and isinstance(alias_info, dict):
            # alias_info maps index_name -> metadata
            idx_name = list(alias_info.keys())[0]
            parsed = _parse_index_datetime(idx_name)
            last_index_time = parsed
            logger.info(f"Last successful index detected: {idx_name} -> {parsed}")
        else:
            logger.warning("No alias 'animal-humane-latest' found - will perform an initial scrape")
            scheduler.run_async(scheduler.scrape_and_index)
    except Exception as e:
        logger.error(f"Error while checking for last index time: {e}")
        # As a conservative approach, run an initial scrape
        scheduler.run_async(scheduler.scrape_and_index)
        last_index_time = None

    # If the last successful index is older than the last scheduled scrape window, perform catch-up
    if last_index_time:
        now = datetime.now()
        # Build list of today's scheduled times (local timezone)
        scheduled_hours = [9, 11, 13, 15, 17, 19]
        missed = []
        # Check today's and yesterday's schedules to cover boundary cases
        for day_offset in [0, -1]:
            day = (now + timedelta(days=day_offset)).replace(hour=0, minute=0, second=0, microsecond=0)
            for hour in scheduled_hours:
                sched_dt = day + timedelta(hours=hour)
                if last_index_time < sched_dt <= now:
                    missed.append(sched_dt)
        if missed:
            logger.info(f"Detected {len(missed)} missed scheduled scrapes since last index: {missed}")
            for m in sorted(missed):
                logger.info(f"Scheduling catch-up scrape for {m}")
                scheduler.run_async(scheduler.scrape_and_index)

    # Setup signal handlers to log SIGTERM and shutdown gracefully
    def _handle_signal(signum, frame):
        logger.warning(f"Received signal {signum}. Shutting down gracefully...")
        try:
            scheduler.executor.shutdown(wait=False)
        except Exception as e:
            logger.warning(f"Error shutting down executor during signal handling: {e}")
        sys.exit(0)

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    # Main loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(5)  # Check every 5 seconds
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {e}", exc_info=True)
    finally:
        logger.info("Shutting down scheduler executor")
        try:
            scheduler.executor.shutdown(wait=False)
        except Exception as e:
            logger.warning(f"Error shutting down executor: {e}")

if __name__ == "__main__":
    main()
