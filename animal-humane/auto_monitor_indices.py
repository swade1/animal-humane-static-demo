#!/usr/bin/env python3
"""
Auto-monitor for new Elasticsearch indices and update timestamp automatically
Runs locally and pushes updates to git when new indices are detected
"""
import json
import requests
import subprocess
import time
from datetime import datetime
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IndexMonitor:
    def __init__(self):
        self.last_known_index = self.load_last_known_index()
        self.repo_path = Path(__file__).parent
        
    def load_last_known_index(self):
        """Load the last known index from our tracking file"""
        tracking_file = Path("last_index_monitored.txt")
        if tracking_file.exists():
            return tracking_file.read_text().strip()
        return None
    
    def save_last_known_index(self, index_name):
        """Save the current index to our tracking file"""
        tracking_file = Path("last_index_monitored.txt")
        tracking_file.write_text(index_name)
        logger.info(f"Saved last known index: {index_name}")
    
    def get_latest_index(self):
        """Get the most recent animal-humane index from Elasticsearch"""
        try:
            response = requests.get('http://localhost:9200/_cat/indices/animal-humane-*?format=json&h=index', timeout=10)
            if response.status_code != 200:
                logger.error(f"Failed to query Elasticsearch: {response.status_code}")
                return None
                
            indices = response.json()
            if not indices:
                logger.warning("No animal-humane indices found")
                return None
                
            # Find the most recent index
            index_names = [idx['index'] for idx in indices]
            latest_index = sorted(index_names)[-1]
            return latest_index
            
        except Exception as e:
            logger.error(f"Error querying Elasticsearch: {e}")
            return None
    
    def update_timestamp_files(self, latest_index):
        """Update timestamp files and push to git"""
        try:
            # Run our existing update script
            result = subprocess.run([
                str(Path('.venv/bin/python')),
                'update_static_data.py'
            ], capture_output=True, text=True, cwd=self.repo_path)
            
            if result.returncode != 0:
                logger.error(f"Update script failed: {result.stderr}")
                return False
            
            logger.info("Successfully updated timestamp files")
            
            # Git add, commit, and push
            git_commands = [
                ['git', 'add', 'react-app/public/api/last-updated.json'],
                ['git', 'commit', '-m', f'Auto-update timestamp for new index: {latest_index}'],
                ['git', 'push', 'origin', 'main']
            ]
            
            for cmd in git_commands:
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.repo_path)
                if result.returncode != 0:
                    logger.error(f"Git command failed: {' '.join(cmd)}")
                    logger.error(f"Error: {result.stderr}")
                    return False
            
            logger.info(f"Successfully pushed timestamp update for {latest_index}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating timestamp: {e}")
            return False
    
    def check_for_new_index(self):
        """Check if there's a new index and update if needed"""
        latest_index = self.get_latest_index()
        
        if not latest_index:
            logger.warning("Could not determine latest index")
            return False
        
        if latest_index != self.last_known_index:
            logger.info(f"🎉 New index detected: {latest_index} (was: {self.last_known_index})")
            
            if self.update_timestamp_files(latest_index):
                self.save_last_known_index(latest_index)
                self.last_known_index = latest_index
                return True
            else:
                logger.error("Failed to update timestamp files")
                return False
        else:
            logger.info(f"No new index (current: {latest_index})")
            return False
    
    def run_continuous_monitoring(self, check_interval_minutes=10):
        """Run continuous monitoring loop"""
        logger.info(f"🔍 Starting continuous monitoring (checking every {check_interval_minutes} minutes)")
        logger.info(f"Current index: {self.last_known_index or 'None'}")
        
        while True:
            try:
                self.check_for_new_index()
                time.sleep(check_interval_minutes * 60)  # Convert to seconds
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

def main():
    import sys
    
    monitor = IndexMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--check-once':
        # Run single check
        logger.info("Running single index check...")
        if monitor.check_for_new_index():
            logger.info("✅ Index update completed")
        else:
            logger.info("ℹ️ No update needed")
    else:
        # Run continuous monitoring
        monitor.run_continuous_monitoring(check_interval_minutes=10)

if __name__ == "__main__":
    main()