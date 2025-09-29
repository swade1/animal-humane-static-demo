"""
Business logic service for dog operations
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
import asyncio

# Simple logging without external dependencies
import logging
logger = logging.getLogger("dog_service")
logging.basicConfig(level=logging.INFO)

class DogService:
    def __init__(self, es_service):
        self.es_service = es_service
    
    async def get_overview_stats(self) -> Dict[str, Any]:
        """Get comprehensive overview statistics"""
        try:
            # Get the data needed for calculations
            availables = await self.es_service.get_current_availables()
            idx = await self.es_service.get_most_recent_index()
            results = await self.es_service.get_dog_groups(availables, idx)
            
            # Calculate totals
            total_unlisted = len(results.get('other_unlisted_dogs', []))
            total_listed = await self.es_service.get_current_listed_count()
            total_listed_and_unlisted = total_listed + total_unlisted
            
            # Get other stats
            new_dog_count = await self.es_service.get_new_dog_count_this_week()
            _, _, _, _, adopted_dog_count = await self.es_service.get_adopted_dogs_this_week()
            trial_adoption_count = len(results.get('trial_adoption_dogs', []))
            
            age_groups = await self.es_service.get_age_groups(idx)
            avg_stay = await self.es_service.get_avg_length_of_stay()
            longest_resident = await self.es_service.get_longest_resident()
            
            # Log the overview data
            await self._log_overview_output(
                total_listed_and_unlisted, 
                new_dog_count, 
                adopted_dog_count, 
                trial_adoption_count
            )
            
            return {
                "total": total_listed_and_unlisted - trial_adoption_count,
                "newThisWeek": new_dog_count,
                "adoptedThisWeek": adopted_dog_count,
                "trialAdoptions": trial_adoption_count,
                "ageGroups": age_groups,
                "avgStay": avg_stay,
                "longestStay": longest_resident
            }
        except Exception as e:
            logger.error(f"Error getting overview stats: {e}")
            raise
    
    async def get_available_dogs(self) -> List[Dict[str, Any]]:
        """Get all currently available dogs"""
        try:
            return await self.es_service.get_current_availables()
        except Exception as e:
            logger.error(f"Error getting available dogs: {e}")
            raise
    
    async def get_dog_by_id(self, dog_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific dog by ID"""
        try:
            return await self.es_service.get_dog_by_id(dog_id)
        except Exception as e:
            logger.error(f"Error getting dog {dog_id}: {e}")
            raise
    
    async def update_dog(self, dog_id: int, dog_update) -> Dict[str, Any]:
        """Update a dog's information"""
        try:
            # Get the latest index for this dog
            latest_index = await self.es_service.get_latest_index_for_dog(dog_id)
            if not latest_index:
                raise ValueError(f"No index found for dog {dog_id}")
            
            # Prepare update data
            update_data = dog_update.dict(exclude_unset=True)
            if 'index' in update_data:
                del update_data['index']  # Don't update the index field
            
            # Perform the update
            result = await self.es_service.update_dog_document(
                latest_index, dog_id, update_data
            )
            
            return {"result": "updated", "dog_id": dog_id}
        except Exception as e:
            logger.error(f"Error updating dog {dog_id}: {e}")
            raise
    
    async def get_recent_adoptions(self) -> List[Dict[str, Any]]:
        """Get recent adoptions"""
        try:
            names, dates, urls, los, _ = await self.es_service.get_adopted_dogs_this_week()
            
            adoptions = []
            for name, date_str, url, length_of_stay in zip(names, dates, urls, los):
                if date_str:
                    try:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S%z')
                        formatted_date = date_obj.strftime('%m/%d/%Y')
                    except (ValueError, TypeError):
                        formatted_date = date_str
                    
                    adoptions.append({
                        "name": name,
                        "date": formatted_date,
                        "url": url,
                        "los": length_of_stay
                    })
            
            return adoptions
        except Exception as e:
            logger.error(f"Error getting recent adoptions: {e}")
            raise
    
    async def get_insights(self) -> Dict[str, Any]:
        """Get insights and analytics"""
        try:
            daily_adoptions = await self.es_service.get_adoptions_per_day()
            return {
                "dailyAdoptions": daily_adoptions
            }
        except Exception as e:
            logger.error(f"Error getting insights: {e}")
            raise
    
    async def get_dog_origins(self) -> List[Dict[str, Any]]:
        """Get dog origin data for mapping"""
        try:
            return await self.es_service.get_origins()
        except Exception as e:
            logger.error(f"Error getting dog origins: {e}")
            raise
    
    async def run_updates(self) -> Dict[str, Any]:
        """Run document updates"""
        try:
            # This would integrate with your existing update logic
            # For now, return a placeholder
            return {"message": "Updates completed", "timestamp": datetime.now().isoformat()}
        except Exception as e:
            logger.error(f"Error running updates: {e}")
            raise
    
    # Private helper methods
    async def _get_total_dogs(self) -> int:
        """Get total number of dogs"""
        return await self.es_service.get_current_listed_count()
    
    async def _get_new_dogs_this_week(self) -> int:
        """Get count of new dogs this week"""
        return await self.es_service.get_new_dog_count_this_week()
    
    async def _get_adopted_dogs_this_week(self) -> int:
        """Get count of adopted dogs this week"""
        _, _, _, _, count = await self.es_service.get_adopted_dogs_this_week()
        return count
    
    async def _get_trial_adoptions(self, results: Dict[str, Any]) -> int:
        """Get count of trial adoptions"""
        return len(results.get('trial_adoption_dogs', []))
    
    async def _get_age_groups(self) -> List[Dict[str, Any]]:
        """Get age group distribution"""
        return await self.es_service.get_age_groups()
    
    async def _get_avg_length_of_stay(self) -> int:
        """Get average length of stay"""
        return await self.es_service.get_avg_length_of_stay()
    
    async def _get_longest_resident(self) -> Dict[str, Any]:
        """Get longest resident information"""
        return await self.es_service.get_longest_resident()
    
    async def get_weekly_age_group_adoptions(self) -> List[Dict[str, Any]]:
        """Get weekly age group adoptions"""
        try:
            return await self.es_service.get_weekly_age_group_adoptions()
        except Exception as e:
            logger.error(f"Error getting weekly age group adoptions: {e}")
            raise
    
    async def get_adoption_percentages_per_origin(self) -> List[Dict[str, Any]]:
        """Get adoption percentages per origin"""
        try:
            return await self.es_service.get_adoption_percentages_per_origin()
        except Exception as e:
            logger.error(f"Error getting adoption percentages per origin: {e}")
            raise
    
    async def run_animal_updates(self) -> Dict[str, Any]:
        """Run animal updates and return results"""
        try:
            availables = await self.es_service.get_current_availables()
            idx = await self.es_service.get_most_recent_index()
            results = await self.es_service.get_dog_groups(availables, idx)
            new_dogs = await self.es_service.get_new_dogs()
            
            # Add new dogs to results
            if "new_dogs" not in results:
                results["new_dogs"] = []
            results["new_dogs"].extend(new_dogs.get("new_dogs", []))
            
            return results
        except Exception as e:
            logger.error(f"Error running animal updates: {e}")
            raise
    
    async def run_document_updates(self) -> Dict[str, Any]:
        """Run document updates"""
        try:
            results = await self.run_animal_updates()
            await self.es_service.update_dogs(results)
            return {
                "update_result": {"detail": "Documents updated."},
                "animal_updates": results
            }
        except Exception as e:
            logger.error(f"Error running document updates: {e}")
            raise
    
    async def format_dog_groups(self, dog_groups: Dict[str, Any]) -> str:
        """Format dog groups for text output"""
        lines = []

        lines.append("New Dogs:")
        for dog in dog_groups.get('new_dogs', []):
            name = dog.get('name', 'Unnamed Dog')
            url = dog.get('url', 'No URL')
            lines.append(f"  {name} - {url}")
        lines.append("")

        lines.append("Adopted/Reclaimed Dogs:")
        for dog in dog_groups.get('adopted_dogs', []):
            name = dog.get('name', 'Unnamed Dog')
            url = dog.get('url', 'No URL')
            lines.append(f"  {name} - {url}")
        lines.append("")

        lines.append("Trial Adoptions:")
        for dog in dog_groups.get('trial_adoption_dogs', []):
            name = dog.get('name', 'Unnamed Dog')
            url = dog.get('url', 'No URL')
            lines.append(f"  {name} - {url}")
        lines.append("")

        lines.append("Other Unlisted Dogs:")
        for dog in dog_groups.get('other_unlisted_dogs', []):
            name = dog.get('name', 'Unnamed Dog')
            url = dog.get('url', 'No URL')
            lines.append(f"  {name} - {url}")
        lines.append("")

        return "\n".join(lines)
    
    async def _log_overview_output(self, total_dogs: int, new: int, adopted: int, trial: int):
        """Log overview output to Elasticsearch"""
        try:
            today_str = datetime.now().strftime('%Y%m%d')
            idx_name = f"logging-{today_str}"

            mapping = {
                "mappings": {
                    "properties": {
                        "timestamp": {"type": "date", "format": "strict_date_optional_time||epoch_millis"},
                        "total_dogs": {"type": "integer"},
                        "new_this_week": {"type": "integer"},
                        "adopted_this_week": {"type": "integer"},
                        "trial_adoptions": {"type": "integer"},
                        "avg_length_of_stay": {"type": "integer"}
                    }
                }
            }
            
            # Create index if it doesn't exist
            await self._run_in_executor(self.es_service.handler.create_index, idx_name, mapping)
            
            doc = {
                "timestamp": datetime.now().isoformat(),
                "total_dogs": total_dogs,
                "new_this_week": new,
                "adopted_this_week": adopted,
                "trial_adoptions": trial
            }
            
            await self._run_in_executor(self.es_service.handler.push_doc_to_elastic, idx_name, doc)
        except Exception as e:
            logger.error(f"Error logging overview output: {e}")
            # Don't raise here as this is just logging
    
    async def _run_in_executor(self, func, *args, **kwargs):
        """Run synchronous function in thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: func(*args, **kwargs)
        )