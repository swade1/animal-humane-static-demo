#!/usr/bin/env python3
"""
Simple, working version of the diff analyzer
"""
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from shelterdog_tracker.elasticsearch_handler import ElasticsearchHandler

class SimpleDiffAnalyzer:
    def __init__(self, output_dir: str = "diff_reports"):
        # Get Elasticsearch host from environment variable for Docker
        es_host = os.getenv('ELASTICSEARCH_HOST', 'http://localhost:9200')
        self.handler = ElasticsearchHandler(host=es_host, index_name="animal-humane-latest")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def get_all_indices(self) -> List[str]:
        """Get all animal-humane indices, sorted by date (most recent first)"""
        try:
            resp = self.handler.es.cat.indices(format="json")
            indices = [item["index"] for item in resp if item["index"].startswith("animal-humane-")]
            indices.sort(reverse=True)
            return indices
        except Exception as e:
            print(f"Error getting all indices: {e}")
            return []
    
    def get_dogs_from_index(self, index_name: str) -> Dict[int, Dict[str, Any]]:
        """Get all dogs from a specific index"""
        try:
            query = {
                "query": {"match_all": {}},
                "_source": ["id", "name", "status", "location", "origin", "intake_date", "length_of_stay_days"],
                "size": 1000
            }
            
            response = self.handler.es.search(index=index_name, body=query)
            
            dogs = {}
            for hit in response['hits']['hits']:
                source = hit['_source']
                dog_id = source.get('id')
                if dog_id:
                    dogs[dog_id] = source
            
            return dogs
            
        except Exception as e:
            print(f"Error getting dogs from index {index_name}: {e}")
            return {}
    
    def analyze_differences(self) -> Optional[Dict[str, Any]]:
        """Simple diff analysis"""
        try:
            all_indices = self.get_all_indices()
            
            if len(all_indices) < 2:
                print("Not enough indices to compare")
                return None
            
            current_index = all_indices[0]  # Most recent
            previous_index = all_indices[1]  # Second most recent
            
            print(f"Comparing {current_index} with {previous_index}")
            
            current_dogs = self.get_dogs_from_index(current_index)
            previous_dogs = self.get_dogs_from_index(previous_index)
            
            print(f"Current index has {len(current_dogs)} dogs")
            print(f"Previous index has {len(previous_dogs)} dogs")
            
            current_ids = set(current_dogs.keys())
            previous_ids = set(previous_dogs.keys())
            
            print(f"Current IDs: {len(current_ids)}")
            print(f"Previous IDs: {len(previous_ids)}")
            print(f"Common IDs: {len(current_ids & previous_ids)}")
            print(f"New IDs: {len(current_ids - previous_ids)}")
            print(f"Adopted IDs: {len(previous_ids - current_ids)}")
            
            # Show some sample IDs for debugging
            if current_ids:
                print(f"Sample current IDs: {list(current_ids)[:5]}")
            if previous_ids:
                print(f"Sample previous IDs: {list(previous_ids)[:5]}")
            if current_ids & previous_ids:
                print(f"Sample common IDs: {list(current_ids & previous_ids)[:5]}")
            
            # NEW DOGS: In current but not in previous
            new_dog_ids = current_ids - previous_ids
            new_dogs = [
                {
                    'id': dog_id,
                    'name': current_dogs[dog_id].get('name'),
                    'status': current_dogs[dog_id].get('status'),
                    'location': current_dogs[dog_id].get('location')
                }
                for dog_id in new_dog_ids
            ]
            
            # ADOPTED/RECLAIMED: In previous but not in current
            adopted_dog_ids = previous_ids - current_ids
            adopted_dogs = [
                {
                    'id': dog_id,
                    'name': previous_dogs[dog_id].get('name'),
                    'status': previous_dogs[dog_id].get('status'),
                    'location': previous_dogs[dog_id].get('location')
                }
                for dog_id in adopted_dog_ids
            ]
            
            # TRIAL ADOPTIONS: Dogs currently in trial adoption
            trial_dogs = []
            for dog_id in current_ids:
                location = current_dogs[dog_id].get('location', '')
                if isinstance(location, list):
                    location = ' '.join(str(item) for item in location)
                location_lower = str(location).lower()
                
                if 'trial adoption' in location_lower:
                    trial_dogs.append({
                        'id': dog_id,
                        'name': current_dogs[dog_id].get('name'),
                        'status': current_dogs[dog_id].get('status'),
                        'location': location
                    })
            
            # Generate timestamp for filenames
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            results = {
                'comparison': {
                    'current_index': current_index,
                    'previous_index': previous_index,
                    'timestamp': datetime.now().isoformat()
                },
                'summary': {
                    'total_current': len(current_dogs),
                    'total_previous': len(previous_dogs),
                    'new_dogs': len(new_dogs),
                    'returned_dogs': 0,  # Simplified for now
                    'adopted_dogs': len(adopted_dogs),
                    'trial_dogs': len(trial_dogs),
                    'unlisted_dogs': 0  # Simplified for now
                },
                'new_dogs': new_dogs,
                'returned_dogs': [],  # Simplified for now
                'adopted_dogs': adopted_dogs,
                'trial_dogs': trial_dogs,
                'unlisted_dogs': [],  # Simplified for now
                'changed_dogs': []
            }
            
            # Save reports
            json_file = self.output_dir / f"diff_report_{timestamp}.json"
            with open(json_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            summary_file = self.output_dir / f"diff_summary_{timestamp}.txt"
            self.save_summary_report(results, summary_file)
            
            print(f"Reports saved:")
            print(f"  - JSON: {json_file}")
            print(f"  - Summary: {summary_file}")
            
            return results
            
        except Exception as e:
            print(f"Error in analyze_differences: {e}")
            return None
    
    def save_summary_report(self, diff_results: Dict[str, Any], filename: Path):
        """Save a human-readable summary report"""
        with open(filename, 'w') as f:
            # New dogs section - always show heading
            f.write("New:\n")
            if diff_results.get('new_dogs'):
                for dog in diff_results['new_dogs']:
                    f.write(f"{dog['name']} - https://new.shelterluv.com/embed/animal/{dog['id']}\n")
            f.write("\n")
            
            # Returned dogs section - always show heading
            f.write("Returned:\n")
            if diff_results.get('returned_dogs'):
                for dog in diff_results['returned_dogs']:
                    f.write(f"{dog['name']} - https://new.shelterluv.com/embed/animal/{dog['id']}\n")
            f.write("\n")
            
            # Adopted/Reclaimed dogs section - always show heading
            f.write("Adopted/Reclaimed:\n")
            if diff_results.get('adopted_dogs'):
                for dog in diff_results['adopted_dogs']:
                    f.write(f"{dog['name']} - https://new.shelterluv.com/embed/animal/{dog['id']}\n")
            f.write("\n")
            
            # Trial Adoptions section - always show heading
            f.write("Trial Adoptions:\n")
            if diff_results.get('trial_dogs'):
                for dog in diff_results['trial_dogs']:
                    f.write(f"{dog['name']} - https://new.shelterluv.com/embed/animal/{dog['id']}\n")
            f.write("\n")
            
            # Available but Temporarily Unlisted section - always show heading
            f.write("Available but Temporarily Unlisted:\n")
            if diff_results.get('unlisted_dogs'):
                for dog in diff_results['unlisted_dogs']:
                    f.write(f"{dog['name']} - https://new.shelterluv.com/embed/animal/{dog['id']}\n")
            f.write("\n")

def main():
    """Run simple diff analysis"""
    analyzer = SimpleDiffAnalyzer()
    results = analyzer.analyze_differences()
    
    if results:
        print("Simple diff analysis completed successfully")
        print(f"Summary: {results['summary']}")
    else:
        print("Simple diff analysis failed or no changes found")

if __name__ == "__main__":
    main()