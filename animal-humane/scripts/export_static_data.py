#!/usr/bin/env python3
"""
Static Data Export Script for Animal Humane Portfolio Demo

This script connects to the running Elasticsearch instance and exports 
API data to static JSON files for the portfolio demonstration.

Usage:
    python scripts/export_static_data.py

Requirements:
    - Running Elasticsearch instance
    - Python packages: requests, elasticsearch (if used)
"""

import json
import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import requests
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('export_static_data.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class StaticDataExporter:
    """
    Exports live API data to static JSON files for portfolio demonstration
    """
    
    def __init__(self, base_url: str = "http://localhost:8000", output_dir: str = "react-app/public/api"):
        """
        Initialize the exporter
        
        Args:
            base_url: Base URL of the running API server
            output_dir: Directory to save static JSON files
        """
        self.base_url = base_url.rstrip('/')
        self.output_dir = Path(output_dir)
        self.session = requests.Session()
        self.session.timeout = 30
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized exporter with base_url={self.base_url}, output_dir={self.output_dir}")

    def test_connection(self) -> bool:
        """
        Test connection to the API server
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                logger.info("✅ Successfully connected to API server")
                return True
            else:
                logger.error(f"❌ API server returned status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to connect to API server: {e}")
            return False

    def fetch_endpoint_data(self, endpoint: str) -> Optional[Dict[Any, Any]]:
        """
        Fetch data from a specific API endpoint
        
        Args:
            endpoint: API endpoint path (e.g., '/api/recent-pupdates')
            
        Returns:
            dict: Response data or None if failed
        """
        url = f"{self.base_url}{endpoint}"
        try:
            logger.info(f"Fetching data from: {url}")
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ Successfully fetched data from {endpoint}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to fetch data from {endpoint}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON response from {endpoint}: {e}")
            return None

    def save_json_file(self, filename: str, data: Dict[Any, Any]) -> bool:
        """
        Save data to a JSON file
        
        Args:
            filename: Name of the output file
            data: Data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        filepath = self.output_dir / filename
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"✅ Saved data to: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save data to {filepath}: {e}")
            return False

    def export_all_data(self) -> bool:
        """
        Export all API endpoints to static JSON files
        
        Returns:
            bool: True if all exports successful, False otherwise
        """
        logger.info("🚀 Starting static data export process...")
        
        # Test connection first
        if not self.test_connection():
            logger.error("❌ Cannot connect to API server. Aborting export.")
            return False
        
        success_count = 0
        total_endpoints = 0
        
        # Define API endpoints to export
        endpoints = [
            ('/api/recent-pupdates', 'recent-pupdates.json'),
            ('/api/live_population', 'live-population.json'),
            ('/api/diff-analysis', 'diff-analysis.json'),
            ('/api/overview', 'overview.json'),
            ('/api/adoptions', 'adoptions.json'),
            ('/api/insights', 'insights.json'),
            ('/api/length-of-stay', 'length-of-stay.json'),
            ('/api/weekly-age-group-adoptions', 'weekly-age-group-adoptions.json'),
            ('/api/dog-origins', 'dog-origins.json'),
        ]
        
        # Export each endpoint
        for endpoint, filename in endpoints:
            total_endpoints += 1
            data = self.fetch_endpoint_data(endpoint)
            
            if data is not None:
                if self.save_json_file(filename, data):
                    success_count += 1
            else:
                logger.warning(f"⚠️ Skipping {filename} due to fetch error")
        
        # Create timestamp file
        total_endpoints += 1
        if self.create_timestamp_file():
            success_count += 1
        
        # Report results
        logger.info(f"📊 Export complete: {success_count}/{total_endpoints} files exported successfully")
        
        if success_count == total_endpoints:
            logger.info("🎉 All exports completed successfully!")
            return True
        else:
            logger.warning(f"⚠️ {total_endpoints - success_count} exports failed")
            return False

    def create_timestamp_file(self) -> bool:
        """
        Create a timestamp file with current export time
        
        Returns:
            bool: True if successful, False otherwise
        """
        current_time = datetime.utcnow().isoformat() + "Z"
        timestamp_data = {
            "timestamp": current_time,
            "human_readable": datetime.now().strftime("%B %d, %Y at %I:%M %p %Z"),
            "export_version": "1.0",
            "data_sources": {
                "recent_pupdates": current_time,
                "live_population": current_time, 
                "diff_analysis": current_time,
                "overview": current_time,
                "adoptions": current_time,
                "insights": current_time,
                "length_of_stay": current_time,
                "weekly_age_group_adoptions": current_time,
                "dog_origins": current_time
            },
            "note": "Static export for portfolio demonstration"
        }
        
        return self.save_json_file('last-updated.json', timestamp_data)


def main():
    """
    Main entry point for the script
    """
    try:
        # Check if we're in the right directory
        if not os.path.exists('react-app'):
            logger.error("❌ react-app directory not found. Run this script from the project root.")
            sys.exit(1)
        
        # Create exporter and run export
        exporter = StaticDataExporter()
        success = exporter.export_all_data()
        
        if success:
            logger.info("✅ Static data export completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Static data export completed with errors")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Export cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error during export: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()