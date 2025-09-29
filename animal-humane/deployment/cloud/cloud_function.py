"""
Google Cloud Function or AWS Lambda version
Triggered by Cloud Scheduler or EventBridge
"""
import json
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def scrape_and_index(event, context):
    """
    Cloud Function entry point for scraping and indexing
    """
    try:
        # Import here to avoid cold start issues
        from shelterdog_tracker.shelter_scraper import ShelterScraper
        from shelterdog_tracker.elasticsearch_handler import ElasticsearchHandler
        
        # Get Elasticsearch host from environment variable
        es_host = os.environ.get('ELASTICSEARCH_HOST', 'http://localhost:9200')
        
        today_str = datetime.now().strftime('%Y%m%d')
        today_time = datetime.now().strftime('%H%M')
        index_name = f"animal-humane-{today_str}-{today_time}"
        
        # Initialize components
        scraper = ShelterScraper(main_url="https://animalhumanenm.org/adopt/adoptable-dogs/")
        handler = ElasticsearchHandler(host=es_host, index_name=index_name)
        
        # Create index
        handler.es.indices.create(index=index_name, ignore=400)
        logger.info(f"Created index: {index_name}")
        
        # Scrape and index
        all_dogs = scraper.scrape_all_dogs()
        handler.push_dogs_to_elasticsearch(all_dogs)
        
        # Update alias
        handler.es.indices.update_aliases(body={
            "actions": [
                {"remove": {"index": "*", "alias": "animal-humane-latest"}},
                {"add": {"index": index_name, "alias": "animal-humane-latest"}},
            ]
        })
        
        result = {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Successfully indexed {len(all_dogs)} dogs to {index_name}',
                'index': index_name,
                'dog_count': len(all_dogs)
            })
        }
        
        logger.info(f"Function completed successfully: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Function failed: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Function execution failed'
            })
        }

def run_diff_analysis(event, context):
    """
    Cloud Function entry point for diff analysis
    """
    try:
        from scheduler.diff_analyzer import DiffAnalyzer
        
        analyzer = DiffAnalyzer(output_dir="/tmp/diff_reports")
        results = analyzer.analyze_differences()
        
        if results:
            # In a real cloud deployment, you'd upload the files to cloud storage
            # For now, we'll return the summary
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Diff analysis completed',
                    'summary': results['summary']
                })
            }
        else:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No differences found or analysis failed'
                })
            }
            
    except Exception as e:
        logger.error(f"Diff analysis failed: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Diff analysis failed'
            })
        }