"""
Async wrapper for Elasticsearch operations
"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

from shelterdog_tracker.elasticsearch_handler import ElasticsearchHandler
from config import config
import logging

logger = logging.getLogger(__name__)

class ElasticsearchService:
    def __init__(self):
        logger.info(f"ElasticsearchService initializing with host: {config.elasticsearch.host}")
        self.handler = ElasticsearchHandler(
            host=config.elasticsearch.host,
            index_name="animal-humane-latest"
        )
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def _run_in_executor(self, func, *args, **kwargs):
        """Run synchronous function in thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            lambda: func(*args, **kwargs)
        )

    async def get_current_availables(self) -> List[Dict[str, Any]]:
        """Get currently available dogs"""
        return await self._run_in_executor(self.handler.get_current_availables)

    async def get_dog_by_id(self, dog_id: int) -> Optional[Dict[str, Any]]:
        """Get dog by ID"""
        return await self._run_in_executor(self.handler.get_dog_by_id, dog_id)

    async def get_current_listed_count(self) -> int:
        """Get current listed count"""
        return await self._run_in_executor(self.handler.get_current_listed_count)

    async def get_new_dog_count_this_week(self) -> int:
        """Get new dog count this week"""
        return await self._run_in_executor(self.handler.get_new_dog_count_this_week)

    async def get_adopted_dogs_this_week(self) -> Tuple[List[str], List[str], List[str], List[int], int]:
        """Get adopted dogs this week"""
        return await self._run_in_executor(self.handler.get_adopted_dog_count_this_week)

    async def get_trial_adoptions(self) -> List[Dict[str, Any]]:
        """Get dogs currently on trial adoption"""
        def _get_trial_adoptions():
            # Get current available dogs
            availables = self.handler.get_current_availables()
            # Filter for dogs with "trial adoption" in location (case insensitive)
            trial_adoptions = [
                dog for dog in availables 
                if 'trial adoption' in dog.get('location', '').lower()
            ]
            return trial_adoptions

        return await self._run_in_executor(_get_trial_adoptions)

    async def get_age_groups(self, index_name: str = None) -> List[Dict[str, Any]]:
        """Get age group distribution"""
        if index_name is None:
            index_name = await self._run_in_executor(self.handler.get_most_recent_index)
        return await self._run_in_executor(self.handler.get_age_groups, index_name)

    async def get_avg_length_of_stay(self) -> int:
        """Get average length of stay"""
        return await self._run_in_executor(self.handler.get_avg_length_of_stay)

    async def get_longest_resident(self) -> Dict[str, Any]:
        """Get longest resident"""
        return await self._run_in_executor(self.handler.get_longest_resident)

    async def get_adoptions_per_day(self) -> List[Dict[str, Any]]:
        """Get adoptions per day"""
        return await self._run_in_executor(self.handler.get_adoptions_per_day)

    async def get_origins(self) -> List[Dict[str, Any]]:
        """Get dog origins"""
        return await self._run_in_executor(self.handler.get_origins)

    async def get_latest_index_for_dog(self, dog_id: int) -> Optional[str]:
        """Get the latest index containing a specific dog"""
        query = {
            "query": {"match": {"id": dog_id}},
            "size": 1,
            "_source": False,
            "sort": [{"_index": {"order": "desc"}}]
        }

        def _search():
            res = self.handler.es.search(index="animal-humane-*", body=query)
            hits = res["hits"]["hits"]
            return hits[0]["_index"] if hits else None

        return await self._run_in_executor(_search)

    async def update_dog_document(self, index_name: str, dog_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a dog document"""
        def _update():
            update_body = {"doc": update_data}
            return self.handler.es.update(
                index=index_name,
                id=str(dog_id),
                body=update_body
            )

        return await self._run_in_executor(_update)

    def __del__(self):
        """Cleanup thread pool on destruction"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)

    async def get_dog_groups(self, availables: List[Dict], index_name: str) -> Dict[str, Any]:
        """Get dog groups (adopted, trial, unlisted)"""
        return await self._run_in_executor(self.handler.get_dog_groups, availables, index_name)

    async def get_weekly_age_group_adoptions(self) -> List[Dict[str, Any]]:
        """Get weekly age group adoptions"""
        return await self._run_in_executor(self.handler.get_weekly_age_group_adoptions)

    async def get_adoption_percentages_per_origin(self) -> List[Dict[str, Any]]:
        """Get adoption percentages per origin"""
        return await self._run_in_executor(self.handler.get_adoption_percentages_per_origin)

    async def get_most_recent_index(self) -> str:
        """Get most recent index name"""
        return await self._run_in_executor(self.handler.get_most_recent_index)

    async def get_new_dogs(self) -> Dict[str, Any]:
        """Get new dogs"""
        return await self._run_in_executor(self.handler.get_new_dogs)

    async def get_length_of_stay_distribution(self) -> Dict[str, Any]:
        """Get length of stay histogram distribution using Sturges formula"""
        return await self._run_in_executor(self.handler.get_length_of_stay_distribution)

    async def get_diff_analysis(self) -> Dict[str, Any]:
        """Get diff analysis data (new, returned, adopted, trial, unlisted dogs)"""
        # Get current available dogs
        availables = await self.get_current_availables()

        # Get most recent index
        index_name = await self.get_most_recent_index()

        # Get dog groups (adopted, trial, unlisted, returned)
        dog_groups = await self.get_dog_groups(availables, index_name)

        # Get new dogs
        new_dogs_data = await self.get_new_dogs()
        new_dogs = new_dogs_data.get("new_dogs", [])

        # Combine results in the format expected by the frontend
        result = {
            "new_dogs": new_dogs,
            "returned_dogs": dog_groups.get("returned_dogs", []),
            "adopted_dogs": dog_groups.get("adopted_dogs", []),
            "trial_adoption_dogs": dog_groups.get("trial_adoption_dogs", []),
            "other_unlisted_dogs": dog_groups.get("other_unlisted_dogs", [])
        }

        # Skip automatic updates for Recent Pupdates tab to avoid seleniumwire dependency
        # The updates can be done separately if needed
        # await self._run_in_executor(self.handler.update_dogs, result)

        return result