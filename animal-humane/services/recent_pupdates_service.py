#!/usr/bin/env python3
"""
Unified Recent Pupdates Service
Consolidates all pupdate sections into a cohesive, robust system
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

from models.recent_pupdates import (
    RecentPupdatesData, DogEntry, DataFreshness, SectionConfig, 
    PupdateSection, DEFAULT_SECTION_CONFIGS
)

logger = logging.getLogger(__name__)


class DataConsistencyManager:
    """Ensures data consistency across sections"""
    
    def ensure_consistency(self, data: RecentPupdatesData) -> RecentPupdatesData:
        """Validate cross-section consistency and fix issues"""
        try:
            # Track all dog IDs across sections
            section_dogs = {
                PupdateSection.NEW_DOGS.value: set(dog.id for dog in data.new_dogs),
                PupdateSection.RETURNED_DOGS.value: set(dog.id for dog in data.returned_dogs),
                PupdateSection.ADOPTED_DOGS.value: set(dog.id for dog in data.adopted_dogs),
                PupdateSection.TRIAL_DOGS.value: set(dog.id for dog in data.trial_dogs),
                PupdateSection.UNLISTED_DOGS.value: set(dog.id for dog in data.unlisted_dogs),
                PupdateSection.AVAILABLE_SOON.value: set(dog.id for dog in data.available_soon)
            }
            
            # Apply exclusion rules based on section configs
            for section_name, section_ids in section_dogs.items():
                config = data.section_configs.get(section_name, DEFAULT_SECTION_CONFIGS.get(section_name))
                if not config:
                    continue
                    
                # Remove dogs that should be excluded based on other sections
                for exclude_section in config.exclusions:
                    exclude_ids = section_dogs.get(exclude_section, set())
                    section_ids -= exclude_ids
            
            # Rebuild sections with filtered dogs
            data.new_dogs = [dog for dog in data.new_dogs if dog.id in section_dogs[PupdateSection.NEW_DOGS.value]]
            data.returned_dogs = [dog for dog in data.returned_dogs if dog.id in section_dogs[PupdateSection.RETURNED_DOGS.value]]
            data.adopted_dogs = [dog for dog in data.adopted_dogs if dog.id in section_dogs[PupdateSection.ADOPTED_DOGS.value]]
            data.trial_dogs = [dog for dog in data.trial_dogs if dog.id in section_dogs[PupdateSection.TRIAL_DOGS.value]]
            data.unlisted_dogs = [dog for dog in data.unlisted_dogs if dog.id in section_dogs[PupdateSection.UNLISTED_DOGS.value]]
            data.available_soon = [dog for dog in data.available_soon if dog.id in section_dogs[PupdateSection.AVAILABLE_SOON.value]]
            
            # Update statistics
            data.total_dogs = sum(len(getattr(data, section)) for section in [
                'new_dogs', 'returned_dogs', 'adopted_dogs', 
                'trial_dogs', 'unlisted_dogs', 'available_soon'
            ])
            
            # Calculate data quality score
            data.data_quality_score = self._calculate_quality_score(data)
            
            return data
            
        except Exception as e:
            logger.error(f"Error ensuring data consistency: {e}")
            data.warnings.append(f"Data consistency check failed: {str(e)}")
            data.data_quality_score = 0.5
            return data
    
    def _calculate_quality_score(self, data: RecentPupdatesData) -> float:
        """Calculate a data quality score based on various factors"""
        score = 1.0
        
        # Penalize for warnings
        score -= len(data.warnings) * 0.1
        
        # Check data freshness
        if data.data_freshness.analysis_timestamp:
            hours_old = (datetime.now() - data.data_freshness.analysis_timestamp).total_seconds() / 3600
            if hours_old > 24:
                score -= 0.2
            elif hours_old > 12:
                score -= 0.1
        
        # Check for missing sections (if total dogs is 0, something might be wrong)
        if data.total_dogs == 0:
            score -= 0.3
        
        return max(0.0, min(1.0, score))


class RecentPupdatesService:
    """Unified service for Recent Pupdates functionality"""
    
    def __init__(self, es_service=None, dog_service=None):
        from services.elasticsearch_service import ElasticsearchService
        from services.dog_service import DogService
        
        self.es_service = es_service or ElasticsearchService()
        self.dog_service = dog_service or DogService(self.es_service)
        self.consistency_manager = DataConsistencyManager()
        
    async def get_recent_pupdates(self) -> RecentPupdatesData:
        """
        Get comprehensive recent pupdates data
        """
        return await self._get_full_analysis()
    
    async def _get_full_analysis(self) -> RecentPupdatesData:
        """Get complete analysis with targeted data sources to avoid scroll issues"""
        logger.info("Starting targeted recent pupdates analysis")
        
        # Initialize data structure
        data = RecentPupdatesData(
            section_configs=DEFAULT_SECTION_CONFIGS.copy(),
            last_updated=datetime.now()
        )
        
        try:
            # Use targeted queries for each section instead of broad diff analysis
            new_dogs_task = self._get_new_dogs()
            returned_dogs_task = self._get_returned_dogs()
            adopted_dogs_task = self._get_adopted_dogs()
            trial_dogs_task = self._get_trial_dogs()
            unlisted_dogs_task = self._get_unlisted_dogs()
            missing_task = self._get_missing_dogs_data()
            
            new_dogs, returned_dogs, adopted_dogs, trial_dogs, unlisted_dogs, missing_dogs = await asyncio.gather(
                new_dogs_task, returned_dogs_task, adopted_dogs_task, trial_dogs_task, unlisted_dogs_task, missing_task
            )
            
            logger.info(f"=== ASYNC GATHER RESULTS ===")
            logger.info(f"missing_dogs result: {missing_dogs}")
            logger.info(f"missing_dogs type: {type(missing_dogs)}")
            logger.info(f"missing_dogs length: {len(missing_dogs) if missing_dogs else 'None'}")
            
            # Populate sections (ensure all results are lists, not None)
            data.new_dogs = self._normalize_diff_section(new_dogs or [], 'new')
            data.returned_dogs = self._normalize_diff_section(returned_dogs or [], 'returned')
            data.adopted_dogs = self._normalize_diff_section(adopted_dogs or [], 'adopted')
            data.trial_dogs = self._normalize_diff_section(trial_dogs or [], 'trial')
            data.unlisted_dogs = self._normalize_diff_section(unlisted_dogs or [], 'unlisted')
            data.available_soon = self._normalize_missing_dogs(missing_dogs or [])
            
            # Set data freshness
            data.data_freshness = DataFreshness(
                analysis_timestamp=datetime.now(),
                elasticsearch_last_update=await self._get_last_es_update(),
                missing_dogs_last_update=await self._get_missing_dogs_last_update()
            )
            
        except Exception as e:
            logger.error(f"Error in targeted analysis: {e}")
            data.warnings.append(f"Data retrieval error: {str(e)}")
        
        # Ensure consistency and apply business rules
        data = self.consistency_manager.ensure_consistency(data)
        
        logger.info(f"Targeted analysis completed: {data.total_dogs} total dogs across all sections")
        return data
    
    async def _get_fallback_data(self) -> RecentPupdatesData:
        """Get fallback data when full analysis fails"""
        logger.info("Using fallback data for recent pupdates")
        
        data = RecentPupdatesData(
            section_configs=DEFAULT_SECTION_CONFIGS.copy(),
            last_updated=datetime.now(),
            data_quality_score=0.3
        )
        
        data.warnings.append("Using fallback data - some sections may be incomplete")
        
        try:
            # Try to get at least missing dogs data
            missing_dogs = await self._get_missing_dogs_data()
            data.available_soon = self._normalize_missing_dogs(missing_dogs)
        except Exception as e:
            logger.error(f"Even fallback data failed: {e}")
            data.warnings.append("All data sources failed")
            data.data_quality_score = 0.0
        
        return data
    
    def _normalize_diff_section(self, raw_data: List[Dict[str, Any]], section_type: str) -> List[DogEntry]:
        """Normalize diff analysis data to DogEntry format"""
        normalized = []
        
        for item in raw_data:
            try:
                # Handle different data formats from different sections
                if section_type == 'new':
                    # New dogs have URL format
                    dog_id = self._extract_id_from_url(item.get('url', ''))
                    if not dog_id:
                        continue
                    
                    entry = DogEntry(
                        id=dog_id,
                        name=item.get('name', 'Unnamed Dog'),
                        url=item.get('url', ''),
                        status=item.get('status'),
                        location=item.get('location'),
                        section_metadata={'source': 'diff_analysis_new'}
                    )
                else:
                    # Other sections have dog_id format, except unlisted which has id
                    if section_type == 'unlisted':
                        dog_id = item.get('id')
                    else:
                        dog_id = item.get('dog_id')
                    
                    if not dog_id:
                        continue
                    
                    entry = DogEntry(
                        id=dog_id,
                        name=item.get('name', 'Unnamed Dog'),
                        url=f"https://new.shelterluv.com/embed/animal/{dog_id}",
                        status=item.get('status'),
                        location=item.get('location'),
                        section_metadata={'source': f'diff_analysis_{section_type}'}
                    )
                
                normalized.append(entry)
                
            except Exception as e:
                logger.warning(f"Error normalizing {section_type} dog data: {e}")
                continue
        
        return normalized
    
    def _normalize_missing_dogs(self, missing_dogs: List[Dict[str, Any]]) -> List[DogEntry]:
        """Normalize missing dogs data to DogEntry format"""
        normalized = []
        
        for item in missing_dogs:
            try:
                entry = DogEntry(
                    id=int(item.get('id', 0)),
                    name=item.get('name', 'Unnamed Dog'),
                    url=item.get('url', ''),
                    section_metadata={'source': 'missing_dogs'}
                )
                normalized.append(entry)
            except Exception as e:
                logger.warning(f"Error normalizing missing dog data: {e}")
                continue
        
        return normalized
    
    def _extract_id_from_url(self, url: str) -> Optional[int]:
        """Extract dog ID from ShelterLuv URL"""
        try:
            if '/animal/' in url:
                return int(url.split('/animal/')[-1])
        except (ValueError, IndexError):
            pass
        return None
    
    async def _get_missing_dogs_data(self) -> List[Dict[str, Any]]:
        """Get available soon dogs by comparing location_info.jsonl with Elasticsearch IDs"""
        return await self._get_available_soon_dogs()
    
    async def _get_missing_dogs_from_file(self) -> List[Dict[str, Any]]:
        """Get missing dogs from text file"""
        try:
            project_root = Path(__file__).resolve().parents[1]
            candidate_paths = [
                project_root / 'react-app' / 'public' / 'missing_dogs.txt',
                project_root / 'missing_dogs.txt'
            ]
            
            for file_path in candidate_paths:
                if file_path.exists():
                    text = file_path.read_text(encoding='utf-8')
                    return self._parse_missing_dogs_text(text)
            
            return []
        except Exception as e:
            logger.error(f"Error reading missing dogs file: {e}")
            return []
    
    def _parse_missing_dogs_text(self, text: str) -> List[Dict[str, Any]]:
        """Parse missing dogs from text format"""
        dogs = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('Missing dogs'):
                continue
            
            # Expected format: "12345: Dog Name"
            if ':' in line:
                try:
                    parts = line.split(':', 1)
                    dog_id = int(parts[0].strip())
                    name = parts[1].strip()
                    
                    dogs.append({
                        'id': dog_id,
                        'name': name,
                        'url': f"https://new.shelterluv.com/embed/animal/{dog_id}"
                    })
                except (ValueError, IndexError):
                    continue
        
        return dogs
    
    async def _get_last_es_update(self) -> Optional[datetime]:
        """Get timestamp of last Elasticsearch update"""
        try:
            index_name = await self.es_service.get_most_recent_index()
            # Extract timestamp from index name if possible
            # Format: animal-humane-YYYYMMDD-HHMM
            if index_name and '-' in index_name:
                parts = index_name.split('-')
                if len(parts) >= 4:
                    date_part = parts[2]  # YYYYMMDD
                    time_part = parts[3]  # HHMM
                    timestamp_str = f"{date_part}{time_part}"
                    return datetime.strptime(timestamp_str, "%Y%m%d%H%M")
        except Exception as e:
            logger.warning(f"Could not determine ES last update: {e}")
        
        return None
    
    async def _get_missing_dogs_last_update(self) -> Optional[datetime]:
        """Get timestamp of last missing dogs file update"""
        try:
            project_root = Path(__file__).resolve().parents[1]
            candidate_paths = [
                project_root / 'react-app' / 'public' / 'missing_dogs.txt',
                project_root / 'missing_dogs.txt'
            ]
            
            for file_path in candidate_paths:
                if file_path.exists():
                    stat = file_path.stat()
                    return datetime.fromtimestamp(stat.st_mtime)
        except Exception as e:
            logger.warning(f"Could not determine missing dogs last update: {e}")
        
        return None
    
    async def _get_new_dogs(self):
        """Get truly new dogs (recent intake, no adoption history)"""
        try:
            # Get current availables from latest index
            current_availables = await self.es_service.get_current_availables()
            
            # Look for dogs that first appeared TODAY only
            from datetime import datetime, timedelta
            today = datetime.now().date()
            logger.info(f"Looking for dogs with intake_date = {today}")
            # Search for dogs that first appeared TODAY
            recent_dogs = []
            for dog in current_availables:
                # Check if this dog has intake_date from today
                intake_date = dog.get('intake_date')
                dog_name = dog.get('name', 'Unknown')
                if intake_date:
                    try:
                        if isinstance(intake_date, str):
                            intake_dt = datetime.strptime(intake_date, '%Y-%m-%d').date()
                        else:
                            intake_dt = intake_date.date() if hasattr(intake_date, 'date') else intake_date
                        
                        logger.info(f"Dog {dog.get('id')} ({dog_name}): intake_date={intake_dt}")
                        if intake_dt == today:
                            logger.info(f"Dog {dog.get('id')} ({dog_name}) is new TODAY")
                            recent_dogs.append(dog)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error parsing intake_date for dog {dog.get('id')} ({dog_name}): {e}")
                        continue
            
            logger.info(f"Found {len(recent_dogs)} dogs with TODAY's intake date")
            
            # Now filter out dogs that have adoption history (those are returned dogs)
            new_dogs = []
            for dog in recent_dogs:
                dog_id = dog.get('id')
                if not dog_id:
                    continue
                    
                # Check if this dog was ever adopted in historical data
                logger.info(f"Checking adoption history for dog {dog_id} ({dog.get('name', 'Unknown')})")
                has_adoption_history = await self._check_adoption_history(dog_id)
                if not has_adoption_history:
                    logger.info(f"Dog {dog_id} has no adoption history - adding to new dogs")
                    new_dogs.append(dog)
                else:
                    logger.info(f"Dog {dog_id} has adoption history - not adding to new dogs")
            
            return new_dogs
        except Exception as e:
            logger.error(f"Error getting new dogs: {e}")
            return []

    async def _get_returned_dogs(self):
        """Get returned dogs (recent intake but with adoption history)"""
        try:
            # Get current availables from latest index
            current_availables = await self.es_service.get_current_availables()
            
            # Look for dogs that appeared TODAY (returns are also "recent")
            from datetime import datetime, timedelta
            today = datetime.now().date()
            
            recent_dogs = []
            for dog in current_availables:
                # Check if this dog has intake_date from today
                intake_date = dog.get('intake_date')
                if intake_date:
                    try:
                        if isinstance(intake_date, str):
                            intake_dt = datetime.strptime(intake_date, '%Y-%m-%d').date()
                        else:
                            intake_dt = intake_date.date() if hasattr(intake_date, 'date') else intake_date
                        
                        if intake_dt == today:
                            recent_dogs.append(dog)
                    except (ValueError, TypeError):
                        continue
            
            # Filter for dogs that have adoption history
            returned_dogs = []
            for dog in recent_dogs:
                dog_id = dog.get('id')
                if not dog_id:
                    continue
                    
                # Check if this dog was ever adopted in historical data
                logger.info(f"Checking adoption history for returned dog {dog_id} ({dog.get('name', 'Unknown')})")
                has_adoption_history = await self._check_adoption_history(dog_id)
                if has_adoption_history:
                    logger.info(f"Dog {dog_id} has adoption history - adding to returned dogs")
                    returned_dogs.append(dog)
                else:
                    logger.info(f"Dog {dog_id} has no adoption history - not adding to returned dogs")
            
            return returned_dogs
        except Exception as e:
            logger.error(f"Error getting returned dogs: {e}")
            return []

    async def _check_adoption_history(self, dog_id: int) -> bool:
        """Check if a dog has adoption history in historical indices"""
        try:
            # Search historical indices for this dog with status 'adopted'
            from datetime import datetime, timedelta
            
            # Check the last 90 days of historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            
            # Generate list of indices to search (recent ones first)
            indices_to_search = []
            current_date = end_date
            while current_date >= start_date:
                date_str = current_date.strftime('%Y%m%d')
                # Check common time patterns 
                for hour in ['0900', '1100', '1300', '1500', '1700', '1900']:
                    index_name = f"animal-humane-{date_str}-{hour}"
                    indices_to_search.append(index_name)
                current_date -= timedelta(days=1)
            
            # Search for adoption records in batches to avoid too many indices
            batch_size = 10
            for i in range(0, len(indices_to_search), batch_size):
                batch_indices = indices_to_search[i:i+batch_size]
                
                # Check if any of these indices exist
                existing_indices = []
                for idx in batch_indices:
                    try:
                        exists = await self._run_in_executor(
                            self.es_service.handler.es.indices.exists, 
                            index=idx
                        )
                        if exists:
                            existing_indices.append(idx)
                    except:
                        continue
                
                if not existing_indices:
                    continue
                
                # Search for adopted status in existing indices
                search_body = {
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"id": dog_id}},
                                {"term": {"status": "adopted"}}
                            ]
                        }
                    },
                    "size": 1
                }
                
                try:
                    index_pattern = ",".join(existing_indices)
                    result = await self._run_in_executor(
                        self.es_service.handler.es.search,
                        index=index_pattern,
                        body=search_body
                    )
                    
                    if result['hits']['total']['value'] > 0:
                        logger.info(f"Found adoption history for dog {dog_id}")
                        return True
                        
                except Exception as e:
                    logger.warning(f"Error searching historical data for dog {dog_id}: {e}")
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking adoption history for dog {dog_id}: {e}")
            return False

    async def _run_in_executor(self, func, *args, **kwargs):
        """Run synchronous function in thread pool"""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        if not hasattr(self, '_executor'):
            self._executor = ThreadPoolExecutor(max_workers=2)
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: func(*args, **kwargs)
        )
    
    async def _get_adopted_dogs(self):
        """Get recently adopted dogs"""
        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=7)
            cutoff_str = cutoff_date.strftime('%Y-%m-%dT%H:%M:%S')
            
            # Search recent indices for adopted dogs
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"status": "adopted"}},
                            {"range": {"timestamp": {"gte": cutoff_str}}}
                        ]
                    }
                },
                "size": 100
            }
            
            # Use latest index only to avoid scroll issues
            most_recent_index = await self.es_service.get_most_recent_index()
            response = self.es_service.es.search(index=most_recent_index, body=query)
            
            return [hit['_source'] for hit in response['hits']['hits']]
        except Exception as e:
            logger.error(f"Error getting adopted dogs: {e}")
            return []
    
    async def _get_trial_dogs(self):
        """Get dogs in trial adoption"""
        try:
            current_availables = await self.es_service.get_current_availables()
            # Filter for dogs with location containing "Trial"
            return [dog for dog in current_availables if 'trial' in dog.get('location', '').lower()]
        except Exception as e:
            logger.error(f"Error getting trial dogs: {e}")
            return []
    
    async def _get_unlisted_dogs(self):
        """Get dogs that are Available but temporarily unlisted (not on current website)"""
        config = DEFAULT_SECTION_CONFIGS[PupdateSection.UNLISTED_DOGS]
        logger.info("Starting unlisted dogs processing...")
        try:
            # Step 1: Get all dog IDs from the most recent index
            most_recent_index = await self.es_service.get_most_recent_index()
            recent_index_result = await self._run_in_executor(
                self.es_service.handler.es.search,
                index=most_recent_index,
                body={"query": {"match_all": {}}, "_source": ["id"], "size": 1000}
            )
            recent_index_dog_ids = {int(hit['_source'].get('id')) for hit in recent_index_result['hits']['hits'] if hit['_source'].get('id')}
            logger.info(f"Most recent index ({most_recent_index}) has {len(recent_index_dog_ids)} dogs")
            
            # Step 2: Get all unique dog IDs that have ever appeared
            all_dogs_result = await self._run_in_executor(
                self.es_service.handler.es.search,
                index='animal-humane-*',
                body={
                    "size": 0,
                    "aggs": {
                        "unique_dogs": {
                            "terms": {"field": "id", "size": 2000}
                        }
                    }
                }
            )
            all_dog_ids = [bucket['key'] for bucket in all_dogs_result['aggregations']['unique_dogs']['buckets']]
            logger.info(f"Found {len(all_dog_ids)} unique dogs across all indices")
            
            # Step 3: For each dog not in most recent index, find their most recent document
            unlisted_dogs = []
            for dog_id in all_dog_ids:
                if int(dog_id) in recent_index_dog_ids:
                    continue  # Skip dogs in most recent index
                    
                # Get most recent document for this dog
                dog_search = {
                    "query": {"term": {"id": int(dog_id)}},
                    "sort": [{"timestamp": {"order": "desc"}}],
                    "size": 1,
                    "_source": ["id", "name", "status", "location", "timestamp"]
                }
                
                dog_result = await self._run_in_executor(
                    self.es_service.handler.es.search,
                    index='animal-humane-*',
                    body=dog_search
                )
                
                if not dog_result['hits']['hits']:
                    continue
                    
                latest_doc = dog_result['hits']['hits'][0]['_source']
                
                # Check all criteria: Available status, non-empty location, and not on Trial Adoption
                if (latest_doc.get('status') == 'Available' and 
                    latest_doc.get('location') and 
                    latest_doc.get('location').strip() and
                    'Trial Adoption' not in latest_doc.get('location', '')):
                    
                    unlisted_dogs.append({
                        'id': latest_doc['id'],
                        'name': latest_doc['name'],
                        'status': latest_doc['status'],
                        'location': latest_doc['location'],
                        'url': f"https://new.shelterluv.com/embed/animal/{latest_doc['id']}"
                    })
                    logger.info(f"Found unlisted Available dog: {latest_doc['name']} (ID: {latest_doc['id']}) at {latest_doc['location']}")
                elif latest_doc.get('status') == 'Available' and 'Trial Adoption' in latest_doc.get('location', ''):
                    logger.info(f"Excluding Trial Adoption dog: {latest_doc['name']} (ID: {latest_doc['id']}) from unlisted")
            
            logger.info(f"Found {len(unlisted_dogs)} dogs that are Available but temporarily unlisted")
            return unlisted_dogs[:20]  # Reasonable limit for unlisted dogs
            
        except Exception as e:
            logger.error(f"Error getting unlisted dogs: {e}")
            return []

    async def _get_available_soon_dogs(self) -> List[Dict[str, Any]]:
        """Get available soon dogs by comparing location_info.jsonl with Elasticsearch IDs"""
        try:
            logger.info("Starting available soon dogs comparison")
            
            # Step 1: Get all unique dog IDs from Elasticsearch
            logger.info("Fetching all unique dog IDs from Elasticsearch")
            es_ids = await self._get_all_elasticsearch_ids()
            if not es_ids:
                logger.warning("No dog IDs found in Elasticsearch")
                return []
            
            print(f"Found {len(es_ids)} unique dog IDs in Elasticsearch")
            logger.info(f"Found {len(es_ids)} unique dog IDs in Elasticsearch")
            
            # Step 2: Get all dogs from location_info.jsonl
            logger.info("Loading dogs from location_info.jsonl")
            location_dogs = await self._load_location_info_dogs()
            if not location_dogs:
                logger.warning("No dogs found in location_info.jsonl")
                return []
            
            print(f"Found {len(location_dogs)} dogs in location_info.jsonl")
            logger.info(f"Found {len(location_dogs)} dogs in location_info.jsonl")
            
            # Step 3: Find dogs in location_info but NOT in Elasticsearch
            location_ids = {int(dog['id']) for dog in location_dogs}
            available_soon_ids = location_ids - es_ids
            
            print(f"Location IDs count: {len(location_ids)}")
            print(f"ES IDs count: {len(es_ids)}")
            print(f"Available Soon IDs count: {len(available_soon_ids)}")
            
            logger.info(f"Location IDs count: {len(location_ids)}")
            logger.info(f"ES IDs count: {len(es_ids)}")
            logger.info(f"Available Soon IDs count: {len(available_soon_ids)}")
            
            # Log some sample IDs for debugging
            sample_location_ids = list(location_ids)[:5]
            sample_es_ids = list(es_ids)[:5]
            print(f"Sample location IDs: {sample_location_ids}")
            print(f"Sample ES IDs: {sample_es_ids}")
            logger.info(f"Sample location IDs: {sample_location_ids}")
            logger.info(f"Sample ES IDs: {sample_es_ids}")
            
            # Step 4: Return the dogs with available soon IDs
            available_soon_dogs = []
            for dog in location_dogs:
                if int(dog['id']) in available_soon_ids:
                    available_soon_dogs.append({
                        'id': int(dog['id']),
                        'name': dog.get('name', 'Unknown'),
                        'url': f"https://new.shelterluv.com/embed/animal/{dog['id']}"
                    })
            
            logger.info(f"Returning {len(available_soon_dogs)} available soon dogs")
            return available_soon_dogs
            
        except Exception as e:
            logger.error(f"Error getting available soon dogs: {e}")
            return []

    async def _get_all_elasticsearch_ids(self) -> set:
        """Get all unique dog IDs from all Elasticsearch indices"""
        try:
            # Use aggregation query across all animal-humane indices
            query = {
                "size": 0,
                "aggs": {
                    "unique_ids": {
                        "terms": {
                            "field": "id",
                            "size": 10000  # Adjust as needed
                        }
                    }
                }
            }
            
            # Query across all indices using the pattern animal-humane-* and _run_in_executor
            result = await self._run_in_executor(
                self.es_service.handler.es.search,
                index="animal-humane-*",
                body=query
            )
            
            all_ids = set()
            if 'aggregations' in result and 'unique_ids' in result['aggregations']:
                buckets = result['aggregations']['unique_ids']['buckets']
                for bucket in buckets:
                    all_ids.add(int(bucket['key']))
            else:
                logger.warning("No aggregations found in Elasticsearch results")
                
            logger.info(f"Found {len(all_ids)} unique dog IDs across all Elasticsearch indices")
            return all_ids
            
        except Exception as e:
            logger.error(f"Error getting Elasticsearch IDs: {e}")
            return set()

    async def _load_location_info_dogs(self) -> List[Dict[str, Any]]:
        """Load dogs from location_info.jsonl file"""
        try:
            # Try multiple possible paths for the file
            from pathlib import Path
            project_root = Path(__file__).resolve().parents[1]
            
            candidate_paths = [
                project_root / 'location_info.jsonl',
                Path('/app/location_info.jsonl'),  # Docker path
                project_root / 'data' / 'location_info.jsonl',
                project_root / 'archived_data' / 'location_info.jsonl'
            ]
            
            location_file = None
            for path in candidate_paths:
                if path.exists():
                    location_file = path
                    break
            
            if not location_file:
                logger.error("location_info.jsonl file not found in any expected location")
                return []
            
            logger.info(f"Loading location_info.jsonl from: {location_file}")
            
            dogs = []
            with open(location_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        dog_data = json.loads(line)
                        if 'id' in dog_data and 'name' in dog_data:
                            dogs.append(dog_data)
                        else:
                            logger.warning(f"Missing id or name in line {line_num}")
                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid JSON on line {line_num}: {e}")
                        continue
            
            logger.info(f"Successfully loaded {len(dogs)} dogs from location_info.jsonl")
            return dogs
            
        except Exception as e:
            logger.error(f"Error loading location_info.jsonl: {e}")
            return []