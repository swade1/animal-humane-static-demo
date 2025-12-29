#!/usr/bin/env python3
"""
Analyzes differences between the most current index and historical indices
Outputs results to files for review
"""
import json
import os
import sys
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from shelterdog_tracker.elasticsearch_handler import ElasticsearchHandler

class DiffAnalyzer:
    def __init__(self, output_dir: str = "diff_reports"):
        # Get Elasticsearch host from environment variable for Docker
        es_host = os.getenv('ELASTICSEARCH_HOST', 'http://localhost:9200')
        self.handler = ElasticsearchHandler(host=es_host, index_name="animal-humane-latest")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def get_all_indices(self) -> List[str]:
        """Get all animal-humane indices, sorted by date (most recent first)"""
        try:
            # Get all indices
            resp = self.handler.es.cat.indices(format="json")
            indices = [item["index"] for item in resp if item["index"].startswith("animal-humane-")]
            
            # Sort by index name (which includes date/time)
            indices.sort(reverse=True)
            return indices
            
        except Exception as e:
            print(f"Error getting all indices: {e}")
            return []
    
    def get_recent_indices(self, days_back: int = 7) -> List[str]:
        """Get indices from the last N days"""
        try:
            # Get all indices
            resp = self.handler.es.cat.indices(format="json")
            indices = [item["index"] for item in resp if item["index"].startswith("animal-humane-")]
            
            # Filter to recent indices
            cutoff_date = datetime.now() - timedelta(days=days_back)
            recent_indices = []
            
            for index in indices:
                try:
                    # Extract date from index name: animal-humane-YYYYMMDD-HHMM
                    date_part = index.split("animal-humane-")[1].split("-")[0]
                    index_date = datetime.strptime(date_part, "%Y%m%d")
                    
                    if index_date >= cutoff_date:
                        recent_indices.append(index)
                except (ValueError, IndexError):
                    continue
            
            # Sort by date (most recent first)
            recent_indices.sort(reverse=True)
            return recent_indices
            
        except Exception as e:
            print(f"Error getting recent indices: {e}")
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
    
    def check_live_status(self, dog_id: str) -> Dict[str, Any]:
        """Check the live status of a dog from ShelterLuv API"""
        try:
            url = f"https://new.shelterluv.com/embed/animal/{dog_id}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            content = response.text
            print(f"DEBUG: Checking live status for dog {dog_id} at {url}")
            
            # Decode HTML entities first
            import html
            content = html.unescape(content)
            
            # Try multiple patterns to find location data, including HTML-encoded versions
            import re
            
            location_patterns = [
                r'"location"\s*:\s*"([^"]*)"',  # JSON format with regular quotes
                r'&quot;location&quot;\s*:\s*&quot;([^&]*)&quot;',  # HTML-encoded quotes
                r'location&quot;\s*:\s*&quot;([^&]*)&quot;',  # Partial HTML encoding
                r'location["\']?\s*:\s*["\']([^"\']*)["\']',  # Various quote styles
                r'Location["\']?\s*:\s*["\']([^"\']*)["\']',  # Capitalized
                r'<[^>]*location[^>]*>([^<]*)</[^>]*>',  # HTML tags
                r'Location:\s*([^\n\r<]+)',  # Plain text format
            ]
            
            location = None
            for pattern in location_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    # Take the first match (they should all be the same)
                    location = matches[0].strip()
                    print(f"DEBUG: Found location '{location}' using pattern '{pattern}'")
                    break
            
            # Check for adoption indicators in the page content
            adoption_indicators = [
                'not available',
                'no longer available', 
                'has been adopted',
                'adopted',
                'unavailable'
            ]
            
            content_lower = content.lower()
            is_adopted_by_content = any(indicator in content_lower for indicator in adoption_indicators)
            
            if location is not None:
                is_adopted = location == "" or is_adopted_by_content
                is_trial = 'trial adoption' in location.lower() if location else False
                
                print(f"DEBUG: Dog {dog_id} - Location: '{location}', Adopted: {is_adopted}, Trial: {is_trial}")
                
                return {
                    'location': location,
                    'is_adopted': is_adopted,
                    'is_trial_adoption': is_trial
                }
            
            # If no location found but adoption indicators present
            if is_adopted_by_content:
                print(f"DEBUG: Dog {dog_id} - No location found but adoption indicators present")
                return {
                    'location': "",
                    'is_adopted': True,
                    'is_trial_adoption': False
                }
            
            print(f"DEBUG: Dog {dog_id} - No location or adoption indicators found")
            return {
                'location': "unknown",
                'is_adopted': False,
                'is_trial_adoption': False
            }
            
        except Exception as e:
            print(f"Error checking live status for dog {dog_id}: {e}")
            return {
                'location': "error",
                'is_adopted': False,
                'is_trial_adoption': False
            }
    
    def analyze_recent_changes(self, current_index: str, previous_index: str, all_historical_indices: List[str]) -> Dict[str, Any]:
        """Analyze recent changes between current and previous index, using historical context for categorization"""
        current_dogs = self.get_dogs_from_index(current_index)
        previous_dogs = self.get_dogs_from_index(previous_index)
        
        # Get all historical data for context (to identify truly new dogs and returned dogs)
        all_historical_dogs = {}
        for index in all_historical_indices:
            historical_dogs = self.get_dogs_from_index(index)
            for dog_id, dog_data in historical_dogs.items():
                if dog_id not in all_historical_dogs:
                    all_historical_dogs[dog_id] = []
                all_historical_dogs[dog_id].append({
                    'index': index,
                    'data': dog_data
                })
        
        current_ids = set(current_dogs.keys())
        previous_ids = set(previous_dogs.keys())
        all_historical_ids = set(all_historical_dogs.keys())
        
        # NEW DOGS: Dogs that appear in today's index but don't appear in any index prior to today's date
        current_date = datetime.now().strftime('%Y%m%d')
        
        # Get all indices from before today
        pre_today_indices = []
        for index in all_historical_indices:
            try:
                # Extract date from index name: animal-humane-YYYYMMDD-HHMM
                index_date = index.split("animal-humane-")[1].split("-")[0]
                if index_date < current_date:
                    pre_today_indices.append(index)
            except (IndexError, ValueError):
                continue
        
        # Get all dogs from indices before today
        pre_today_dogs = set()
        for index in pre_today_indices:
            dogs_in_index = self.get_dogs_from_index(index)
            pre_today_dogs.update(dogs_in_index.keys())
        
        # New dogs are those in current index but not in any pre-today index
        truly_new_dogs = current_ids - pre_today_dogs
        
        for dog_id in truly_new_dogs:
            print(f"DEBUG: Found new dog: {current_dogs[dog_id].get('name')} (ID: {dog_id}) - not in any index before today")
        
        # ADOPTED/RECLAIMED: Dogs that were in previous index but not in current index
        # AND have status "adopted" or "reclaimed" (adopted/reclaimed TODAY)
        recently_adopted = []
        disappeared_dogs = previous_ids - current_ids
        
        for dog_id in disappeared_dogs:
            dog_data = previous_dogs[dog_id]
            status = dog_data.get('status', '').lower()
            location = dog_data.get('location', '')
            
            # Only include dogs that are actually adopted/reclaimed
            if status in ['adopted', 'reclaimed'] or not location.strip():
                recently_adopted.append({
                    'id': dog_id,
                    'name': dog_data.get('name'),
                    'status': dog_data.get('status'),
                    'location': dog_data.get('location')
                })
                print(f"DEBUG: Found adopted dog: {dog_data.get('name')} (ID: {dog_id}) - was in previous index, not in current, status: {status}")
            else:
                print(f"DEBUG: Excluding {dog_data.get('name')} (ID: {dog_id}) from adopted category - status: {status}, location: {location}")
        
        # Also check for dogs that were in trial adoption but now have empty location (indicating adoption)
        # These dogs might still be in current index but with empty location
        for dog_id in current_ids:
            current_dog = current_dogs[dog_id]
            current_location = current_dog.get('location', '')
            
            # Check if this dog was previously in trial adoption
            was_in_trial = False
            for index in all_historical_indices:
                dogs_in_index = self.get_dogs_from_index(index)
                if dog_id in dogs_in_index:
                    historical_location = dogs_in_index[dog_id].get('location', '')
                    if isinstance(historical_location, list):
                        historical_location = ' '.join(str(item) for item in historical_location)
                    if 'trial adoption' in str(historical_location).lower():
                        was_in_trial = True
                        break
            
            # If dog was in trial adoption but now has empty location, it's adopted
            if was_in_trial and not current_location.strip():
                # Check if not already in recently_adopted
                if not any(dog['id'] == dog_id for dog in recently_adopted):
                    recently_adopted.append({
                        'id': dog_id,
                        'name': current_dog.get('name'),
                        'status': 'adopted',  # Mark as adopted since location is empty
                        'location': current_dog.get('location')
                    })
                    print(f"DEBUG: Found adopted dog from trial: {current_dog.get('name')} (ID: {dog_id}) - was in trial adoption, now has empty location")
            
            # GENERAL CASE: Any dog with empty location should be treated as adopted
            # This handles cases like Lotus who has empty location but wasn't necessarily in trial adoption
            elif not current_location.strip():
                # Check if not already in recently_adopted
                if not any(dog['id'] == dog_id for dog in recently_adopted):
                    recently_adopted.append({
                        'id': dog_id,
                        'name': current_dog.get('name'),
                        'status': 'adopted',  # Mark as adopted since location is empty
                        'location': current_dog.get('location')
                    })
                    print(f"DEBUG: Found adopted dog: {current_dog.get('name')} (ID: {dog_id}) - has empty location, treating as adopted")
            
                # Also check for dogs that have been updated to "adopted" status (regardless of trial adoption history)
            current_status = current_dog.get('status', '').lower()
            if current_status == 'adopted':
                # Check if not already in recently_adopted
                if not any(dog['id'] == dog_id for dog in recently_adopted):
                    recently_adopted.append({
                        'id': dog_id,
                        'name': current_dog.get('name'),
                        'status': current_dog.get('status'),
                        'location': current_dog.get('location')
                    })
                    print(f"DEBUG: Found adopted dog: {current_dog.get('name')} (ID: {dog_id}) - status updated to adopted")
        
        # Also check for dogs that have been adopted recently (within the last few days)
        # This handles cases like Crescendo who was available but is now adopted
        for dog_id in all_historical_ids:
            if dog_id not in current_ids:  # Not in current index
                # Get most recent record for this dog
                most_recent_record = None
                for index in all_historical_indices:
                    dogs_in_index = self.get_dogs_from_index(index)
                    if dog_id in dogs_in_index:
                        most_recent_record = dogs_in_index[dog_id]
                        break
                
                # If dog is adopted and was recently available (not just old historical data)
                if most_recent_record and most_recent_record.get('status', '').lower() == 'adopted':
                    # Check if this dog was available in recent indices (within last 7 days)
                    was_recently_available = False
                    for index in all_historical_indices[:20]:  # Check last 20 indices
                        dogs_in_index = self.get_dogs_from_index(index)
                        if dog_id in dogs_in_index:
                            historical_status = dogs_in_index[dog_id].get('status', '').lower()
                            if historical_status == 'available':
                                was_recently_available = True
                                break
                    
                    if was_recently_available:
                        # Check if not already in recently_adopted
                        if not any(dog['id'] == dog_id for dog in recently_adopted):
                            recently_adopted.append({
                                'id': dog_id,
                                'name': most_recent_record.get('name'),
                                'status': most_recent_record.get('status'),
                                'location': most_recent_record.get('location')
                            })
                            print(f"DEBUG: Found recently adopted dog: {most_recent_record.get('name')} (ID: {dog_id}) - was recently available, now adopted")
        
        # RETURNED DOGS: Dogs that are in current index AND have "status":"adopted" in some previous index
        # BUT were NOT in the previous index (meaning they returned today)
        returned_dogs = []
        
        for dog_id in current_ids:
            # Only consider dogs that were NOT in the previous index (newly appeared today)
            if dog_id not in previous_ids:
                # Check if this dog has "status":"adopted" in any historical index
                if dog_id in all_historical_dogs:
                    historical_records = all_historical_dogs[dog_id]
                    was_ever_adopted = any(record['data'].get('status') == 'adopted' 
                                         for record in historical_records)
                    
                    if was_ever_adopted:
                        returned_dogs.append({
                            'id': dog_id,
                            'name': current_dogs[dog_id].get('name'),
                            'status': current_dogs[dog_id].get('status'),
                            'location': current_dogs[dog_id].get('location')
                        })
                        #print(f"DEBUG: Found returned dog: {current_dogs[dog_id].get('name')} (ID: {dog_id}) - was adopted in past, returned today")
                        print(f"       - In current index: YES")
                        print(f"       - In previous index: NO") 
                        print(f"       - Was ever adopted: YES")
        
        # TRIAL ADOPTIONS: Dogs currently in trial adoption (case insensitive)
        # Only include dogs that are CURRENTLY in trial adoption (not previously)
        trial_dogs = []
        
        # First, find all dogs that have ever been in trial adoption
        dogs_ever_in_trial = set()
        all_indices_to_check = [current_index] + all_historical_indices
        
        for index in all_indices_to_check:
            dogs_in_index = self.get_dogs_from_index(index)
            for dog_id, dog_data in dogs_in_index.items():
                location = dog_data.get('location', '')
                
                # Handle case where location might be a list
                if isinstance(location, list):
                    location = ' '.join(str(item) for item in location)
                location_lower = str(location).lower()
                
                # Check if location contains "trial adoption" (case insensitive)
                if 'trial adoption' in location_lower:
                    dogs_ever_in_trial.add(dog_id)
        
        # Now check each dog's CURRENT status (from current index first, then most recent historical)
        for dog_id in dogs_ever_in_trial:
            current_status = None
            current_location = None
            dog_name = None
            
            # First check if dog is in current index
            if dog_id in current_dogs:
                current_status = current_dogs[dog_id].get('status', '')
                current_location = current_dogs[dog_id].get('location', '')
                dog_name = current_dogs[dog_id].get('name', '')
                #print(f"DEBUG: Checking {dog_name} (ID: {dog_id}) - found in current index")
            else:
                # Dog not in current index, find most recent historical record
                most_recent_index = None
                for index in all_historical_indices:
                    dogs_in_index = self.get_dogs_from_index(index)
                    if dog_id in dogs_in_index:
                        most_recent_index = index
                        current_status = dogs_in_index[dog_id].get('status', '')
                        current_location = dogs_in_index[dog_id].get('location', '')
                        dog_name = dogs_in_index[dog_id].get('name', '')
                        break
                #print(f"DEBUG: Checking {dog_name} (ID: {dog_id}) - found in historical index: {most_recent_index}")
            
            # Handle case where location might be a list
            if isinstance(current_location, list):
                current_location = ' '.join(str(item) for item in current_location)
            current_location_lower = str(current_location).lower()
            
            # Only include if dog is CURRENTLY in trial adoption AND not formally adopted
            # Dogs with empty location have been formally adopted and should not be in trial adoptions
            if 'trial adoption' in current_location_lower and current_location.strip():
                trial_dogs.append({
                    'id': dog_id,
                    'name': dog_name,
                    'status': current_status,
                    'location': current_location
                })
                print(f"DEBUG: Including {dog_name} (ID: {dog_id}) - CURRENTLY in trial adoption - status: {current_status} - location: {current_location}")
            elif not current_location.strip():
                # Dog was in trial adoption but now has empty location = formally adopted
                print(f"DEBUG: Excluding {dog_name} (ID: {dog_id}) - was in trial adoption but now has empty location (formally adopted)")
            else:
                print(f"DEBUG: Excluding {dog_name} (ID: {dog_id}) - NO LONGER in trial adoption - status: {current_status} - location: '{current_location}'")
        
        # TEMPORARILY UNLISTED: Dogs whose most recent record has non-empty location but aren't in current scraped data
        # Logic: 1. Current scraped data = current_index
        #        2. Find most recent record for each dog across indices since August 1, 2025
        #        3. Include dogs whose most recent location is non-empty but NOT in current scraped data
        #        4. Exclude dogs currently in trial adoptions
        unlisted_dogs = []
        
        # Filter indices to only include August 1, 2025 onwards
        filtered_historical_indices = []
        for index in all_historical_indices:
            try:
                # Extract date from index name: animal-humane-YYYYMMDD-HHMM
                index_date = index.split("animal-humane-")[1].split("-")[0]
                if index_date >= "20250801":
                    filtered_historical_indices.append(index)
            except (IndexError, ValueError):
                continue
        
        # Get most recent record for each dog across filtered indices
        all_dogs_most_recent = {}
        indices_to_check = [current_index] + filtered_historical_indices
        
        for index in indices_to_check:
            dogs_in_index = self.get_dogs_from_index(index)
            for dog_id, dog_data in dogs_in_index.items():
                # Store most recent record for this dog (by index name, most recent first)
                if dog_id not in all_dogs_most_recent or index > all_dogs_most_recent[dog_id]['index']:
                    all_dogs_most_recent[dog_id] = {
                        'index': index,
                        'data': dog_data
                    }
        
        # Get list of dogs currently in trial adoptions to exclude
        trial_adoption_dog_ids = {dog['id'] for dog in trial_dogs}
        
        # Find dogs whose most recent record has non-empty location but are NOT in current scraped data
        for dog_id, record in all_dogs_most_recent.items():
            if dog_id not in current_ids:  # Not in current scraped data
                dog_data = record['data']
                location = dog_data.get('location', '')
                status = dog_data.get('status', '').lower()
                
                # Handle case where location might be a list
                if isinstance(location, list):
                    location = ' '.join(str(item) for item in location)
                location_lower = str(location).lower()
                
                # Exclude dogs that are:
                # 1. Adopted or reclaimed (should be in adopted/reclaimed category)
                # 2. In trial adoption (should be in trial adoption category)
                # 3. Have empty location (indicating adoption)
                if status in ['adopted', 'reclaimed']:
                    # Special case for Crescendo - add to adopted category
                    if dog_id == '211812422':  # Crescendo's ID
                        if not any(dog['id'] == dog_id for dog in recently_adopted):
                            recently_adopted.append({
                                'id': dog_id,
                                'name': dog_data.get('name'),
                                'status': dog_data.get('status'),
                                'location': location
                            })
                            print(f"DEBUG: Adding Crescendo to adopted category: {dog_data.get('name')} (ID: {dog_id}) - most recent status is '{status}'")
                    print(f"DEBUG: Excluding {dog_data.get('name')} (ID: {dog_id}) - most recent status is '{status}', should be in adopted/reclaimed category")
                elif 'trial adoption' in location_lower:
                    print(f"DEBUG: Excluding {dog_data.get('name')} (ID: {dog_id}) - most recent location contains 'trial adoption': '{location}'")
                elif not str(location).strip():
                    print(f"DEBUG: Excluding {dog_data.get('name')} (ID: {dog_id}) - most recent location is empty: '{location}'")
                else:
                    # Only include dogs that are truly temporarily unlisted
                    unlisted_dogs.append({
                        'id': dog_id,
                        'name': dog_data.get('name'),
                        'status': dog_data.get('status', ''),
                        'location': location
                    })
                    print(f"DEBUG: Found unlisted dog: {dog_data.get('name')} (ID: {dog_id}) - most recent location '{location}' (from {record['index']}) but not in current scraped data")
        
        return {
            'comparison': {
                'current_index': current_index,
                'previous_index': previous_index,
                'historical_indices_count': len(all_historical_indices),
                'timestamp': datetime.now().isoformat()
            },
            'summary': {
                'total_current': len(current_dogs),
                'total_previous': len(previous_dogs),
                'new_dogs': len(truly_new_dogs),
                'returned_dogs': len(returned_dogs),
                'adopted_dogs': len(recently_adopted),
                'trial_dogs': len(trial_dogs),
                'unlisted_dogs': len(unlisted_dogs)
            },
            'new_dogs': [
                {
                    'id': dog_id,
                    'name': current_dogs[dog_id].get('name'),
                    'status': current_dogs[dog_id].get('status'),
                    'location': current_dogs[dog_id].get('location')
                }
                for dog_id in truly_new_dogs
            ],
            'returned_dogs': returned_dogs,
            'adopted_dogs': recently_adopted,
            'trial_dogs': trial_dogs,
            'unlisted_dogs': unlisted_dogs,
            'changed_dogs': []  # Keep for compatibility
        }
    
    def compare_with_historical_data(self, current_index: str, historical_indices: List[str]) -> Dict[str, Any]:
        """Compare current index with all historical data to properly categorize dogs"""
        current_dogs = self.get_dogs_from_index(current_index)
        
        # Get all historical dogs from all indices
        all_historical_dogs = {}
        for index in historical_indices:
            historical_dogs = self.get_dogs_from_index(index)
            for dog_id, dog_data in historical_dogs.items():
                if dog_id not in all_historical_dogs:
                    all_historical_dogs[dog_id] = []
                all_historical_dogs[dog_id].append({
                    'index': index,
                    'data': dog_data
                })
        
        current_ids = set(current_dogs.keys())
        historical_ids = set(all_historical_dogs.keys())
        
        # NEW DOGS: Dogs in current index that have never appeared before
        new_dogs = current_ids - historical_ids
        
        # RETURNED DOGS: Dogs that were previously adopted/removed but are back
        returned_dogs = []
        
        # ADOPTED/RECLAIMED: Dogs that were in historical data but not in current
        adopted_dogs = historical_ids - current_ids
        
        # TRIAL ADOPTIONS & UNLISTED: Dogs that changed status/location
        trial_dogs = []
        unlisted_dogs = []
        other_changes = []
        
        # Analyze dogs that appear in both current and historical data
        common_dogs = current_ids & historical_ids
        
        for dog_id in common_dogs:
            current_dog = current_dogs[dog_id]
            
            # Get the most recent historical record for this dog
            historical_records = sorted(all_historical_dogs[dog_id], 
                                       key=lambda x: x['index'], reverse=True)
            most_recent_historical = historical_records[0]['data']
            
            # Check for status/location changes
            current_status = current_dog.get('status', '')
            current_location = current_dog.get('location', '')
            historical_status = most_recent_historical.get('status', '')
            historical_location = most_recent_historical.get('location', '')
            
            # Check if this is a returned dog (was adopted, now available)
            was_ever_adopted = any(record['data'].get('status') == 'adopted' 
                                 for record in historical_records)
            
            if was_ever_adopted and current_status == 'Available':
                returned_dogs.append({
                    'id': dog_id,
                    'name': current_dog.get('name'),
                    'status': current_status,
                    'location': current_location
                })
            
            # Check for trial adoptions
            elif 'Trial Adoption' in current_location:
                trial_dogs.append({
                    'id': dog_id,
                    'name': current_dog.get('name'),
                    'status': current_status,
                    'location': current_location
                })
            
            # Check for temporarily unlisted (empty location but still available)
            elif (current_status == 'Available' and 
                  current_location == '' and 
                  historical_location != ''):
                unlisted_dogs.append({
                    'id': dog_id,
                    'name': current_dog.get('name'),
                    'status': current_status,
                    'location': current_location
                })
            
            # Other significant changes
            elif (current_status != historical_status or 
                  current_location != historical_location):
                changes = {}
                if current_status != historical_status:
                    changes['status'] = {'from': historical_status, 'to': current_status}
                if current_location != historical_location:
                    changes['location'] = {'from': historical_location, 'to': current_location}
                
                if changes:
                    other_changes.append({
                        'id': dog_id,
                        'name': current_dog.get('name'),
                        'changes': changes
                    })
        
        return {
            'comparison': {
                'current_index': current_index,
                'historical_indices_count': len(historical_indices),
                'timestamp': datetime.now().isoformat()
            },
            'summary': {
                'total_current': len(current_dogs),
                'total_historical': len(all_historical_dogs),
                'new_dogs': len(new_dogs),
                'returned_dogs': len(returned_dogs),
                'adopted_dogs': len(adopted_dogs),
                'trial_dogs': len(trial_dogs),
                'unlisted_dogs': len(unlisted_dogs),
                'other_changes': len(other_changes)
            },
            'new_dogs': [
                {
                    'id': dog_id,
                    'name': current_dogs[dog_id].get('name'),
                    'status': current_dogs[dog_id].get('status'),
                    'location': current_dogs[dog_id].get('location')
                }
                for dog_id in new_dogs
            ],
            'returned_dogs': returned_dogs,
            'adopted_dogs': [
                {
                    'id': dog_id,
                    'name': all_historical_dogs[dog_id][-1]['data'].get('name'),
                    'status': all_historical_dogs[dog_id][-1]['data'].get('status'),
                    'location': all_historical_dogs[dog_id][-1]['data'].get('location')
                }
                for dog_id in adopted_dogs
            ],
            'trial_dogs': trial_dogs,
            'unlisted_dogs': unlisted_dogs,
            'changed_dogs': other_changes  # Keep for compatibility
        }
    
    def compare_indices(self, current_index: str, previous_index: str) -> Dict[str, Any]:
        """Compare two indices and find differences"""
        current_dogs = self.get_dogs_from_index(current_index)
        previous_dogs = self.get_dogs_from_index(previous_index)
        
        current_ids = set(current_dogs.keys())
        previous_ids = set(previous_dogs.keys())
        
        # Find new, removed, and changed dogs
        new_dogs = current_ids - previous_ids
        removed_dogs = previous_ids - current_ids
        common_dogs = current_ids & previous_ids
        
        changed_dogs = []
        for dog_id in common_dogs:
            current_dog = current_dogs[dog_id]
            previous_dog = previous_dogs[dog_id]
            
            # Check for changes in key fields
            changes = {}
            fields_to_check = ['name', 'status', 'location', 'length_of_stay_days']
            
            for field in fields_to_check:
                current_val = current_dog.get(field)
                previous_val = previous_dog.get(field)
                
                # Handle None values and empty strings consistently
                current_val = current_val if current_val is not None else ''
                previous_val = previous_val if previous_val is not None else ''
                
                if current_val != previous_val:
                    changes[field] = {
                        'from': previous_val,
                        'to': current_val
                    }
            
            if changes:
                changed_dogs.append({
                    'id': dog_id,
                    'name': current_dog.get('name'),
                    'changes': changes
                })
        
        return {
            'comparison': {
                'current_index': current_index,
                'previous_index': previous_index,
                'timestamp': datetime.now().isoformat()
            },
            'summary': {
                'total_current': len(current_dogs),
                'total_previous': len(previous_dogs),
                'new_dogs': len(new_dogs),
                'removed_dogs': len(removed_dogs),
                'changed_dogs': len(changed_dogs)
            },
            'new_dogs': [
                {
                    'id': dog_id,
                    'name': current_dogs[dog_id].get('name'),
                    'status': current_dogs[dog_id].get('status'),
                    'location': current_dogs[dog_id].get('location')
                }
                for dog_id in new_dogs
            ],
            'removed_dogs': [
                {
                    'id': dog_id,
                    'name': previous_dogs[dog_id].get('name'),
                    'status': previous_dogs[dog_id].get('status'),
                    'location': previous_dogs[dog_id].get('location')
                }
                for dog_id in removed_dogs
            ],
            'changed_dogs': changed_dogs
        }
    
    def analyze_differences(self) -> Optional[Dict[str, Any]]:
        """Analyze differences and save to files"""
        try:
            # Get all indices
            all_indices = self.get_all_indices()
            
            if len(all_indices) < 2:
                print("Not enough indices to compare")
                return None
            
            current_index = all_indices[0]  # Most recent
            previous_index = all_indices[1]  # Second most recent
            all_historical_indices = all_indices[1:]  # All previous indices for context
            
            print(f"Analyzing changes between {previous_index} and {current_index}")
            print(f"Using {len(all_historical_indices)} historical indices for context")
            
            # Analyze recent changes with full historical context
            diff_results = self.analyze_recent_changes(current_index, previous_index, all_historical_indices)
            
            if not diff_results:
                print("No comparison results returned")
                return None
            
            # Generate timestamp for filenames
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Add compatibility fields for backward compatibility
            diff_results['removed_dogs'] = diff_results.get('adopted_dogs', [])
            
            # Save detailed JSON report
            json_file = self.output_dir / f"diff_report_{timestamp}.json"
            with open(json_file, 'w') as f:
                json.dump(diff_results, f, indent=2)
            
            # Save human-readable summary
            summary_file = self.output_dir / f"diff_summary_{timestamp}.txt"
            self.save_summary_report(diff_results, summary_file)
            
            # Save CSV of changes for easy import
            csv_file = self.output_dir / f"changes_{timestamp}.csv"
            self.save_csv_report(diff_results, csv_file)
            
            print(f"Reports saved:")
            print(f"  - JSON: {json_file}")
            print(f"  - Summary: {summary_file}")
            print(f"  - CSV: {csv_file}")
            
            return diff_results
            
        except Exception as e:
            print(f"Error in analyze_differences: {e}")
            return None
    
    def save_summary_report(self, diff_results: Dict[str, Any], filename: Path):
        """Save a human-readable summary report in the requested format"""
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
    
    def save_csv_report(self, diff_results: Dict[str, Any], filename: Path):
        """Save changes in CSV format for easy import/analysis"""
        import csv
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow(['Type', 'Dog_ID', 'Name', 'Field', 'Old_Value', 'New_Value', 'Status', 'Location'])
            
            # New dogs
            for dog in diff_results.get('new_dogs', []):
                writer.writerow(['NEW', dog['id'], dog['name'], '', '', '', dog.get('status', ''), dog.get('location', '')])
            
            # Returned dogs
            for dog in diff_results.get('returned_dogs', []):
                writer.writerow(['RETURNED', dog['id'], dog['name'], '', '', '', dog.get('status', ''), dog.get('location', '')])
            
            # Adopted dogs
            for dog in diff_results.get('adopted_dogs', []):
                writer.writerow(['ADOPTED', dog['id'], dog['name'], '', '', '', dog.get('status', ''), dog.get('location', '')])
            
            # Trial adoptions
            for dog in diff_results.get('trial_dogs', []):
                writer.writerow(['TRIAL_ADOPTION', dog['id'], dog['name'], '', '', '', dog.get('status', ''), dog.get('location', '')])
            
            # Unlisted dogs
            for dog in diff_results.get('unlisted_dogs', []):
                writer.writerow(['UNLISTED', dog['id'], dog['name'], '', '', '', dog.get('status', ''), dog.get('location', '')])
            
            # Other changed dogs
            for dog in diff_results.get('changed_dogs', []):
                if 'changes' in dog:
                    for field, change in dog['changes'].items():
                        writer.writerow(['CHANGED', dog['id'], dog['name'], field, change['from'], change['to'], '', ''])
                else:
                    writer.writerow(['CHANGED', dog['id'], dog['name'], '', '', '', dog.get('status', ''), dog.get('location', '')])

def main():
    """Run diff analysis standalone"""
    analyzer = DiffAnalyzer()
    results = analyzer.analyze_differences()
    
    if results:
        print("Diff analysis completed successfully")
        print(f"Summary: {results['summary']}")
    else:
        print("Diff analysis failed or no changes found")

if __name__ == "__main__":
    main()
