"""
Unit tests for DogService
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from services.dog_service import DogService
from services.elasticsearch_service import ElasticsearchService
from models.api_models import DogUpdate

@pytest.fixture
def mock_es_service():
    """Mock Elasticsearch service"""
    service = Mock(spec=ElasticsearchService)
    
    # Make all methods async
    for method_name in dir(ElasticsearchService):
        if not method_name.startswith('_') and callable(getattr(ElasticsearchService, method_name)):
            setattr(service, method_name, AsyncMock())
    
    return service

@pytest.fixture
def dog_service(mock_es_service):
    """DogService instance with mocked dependencies"""
    return DogService(mock_es_service)

class TestDogService:
    
    @pytest.mark.asyncio
    async def test_get_overview_stats_success(self, dog_service, mock_es_service):
        """Test successful overview stats retrieval"""
        # Setup mock responses
        mock_es_service.get_current_listed_count.return_value = 50
        mock_es_service.get_new_dog_count_this_week.return_value = 5
        mock_es_service.get_adopted_dogs_this_week.return_value = ([], [], [], [], 3)
        mock_es_service.get_age_groups.return_value = [
            {"age_group": "Adult", "count": 30},
            {"age_group": "Puppy", "count": 15},
            {"age_group": "Senior", "count": 5}
        ]
        mock_es_service.get_avg_length_of_stay.return_value = 25
        mock_es_service.get_longest_resident.return_value = {
            "name": "Buddy", "days": 120, "url": "http://example.com"
        }
        
        # Execute
        result = await dog_service.get_overview_stats()
        
        # Verify
        assert result["total"] == 50  # 50 total - 0 trials
        assert result["newThisWeek"] == 5
        assert result["adoptedThisWeek"] == 3
        assert result["trialAdoptions"] == 0
        assert len(result["ageGroups"]) == 3
        assert result["avgStay"] == 25
        assert result["longestStay"]["name"] == "Buddy"
    
    @pytest.mark.asyncio
    async def test_get_dog_by_id_found(self, dog_service, mock_es_service):
        """Test retrieving existing dog by ID"""
        expected_dog = {
            "id": 123,
            "name": "Buddy",
            "status": "Available",
            "breed": "Golden Retriever"
        }
        mock_es_service.get_dog_by_id.return_value = expected_dog
        
        result = await dog_service.get_dog_by_id(123)
        
        assert result == expected_dog
        mock_es_service.get_dog_by_id.assert_called_once_with(123)
    
    @pytest.mark.asyncio
    async def test_get_dog_by_id_not_found(self, dog_service, mock_es_service):
        """Test retrieving non-existent dog by ID"""
        mock_es_service.get_dog_by_id.return_value = None
        
        result = await dog_service.get_dog_by_id(999)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_dog_success(self, dog_service, mock_es_service):
        """Test successful dog update"""
        dog_update = DogUpdate(name="Updated Name", status="adopted")
        mock_es_service.get_latest_index_for_dog.return_value = "animal-humane-20250101-1200"
        mock_es_service.update_dog_document.return_value = {"result": "updated"}
        
        result = await dog_service.update_dog(123, dog_update)
        
        assert result["result"] == "updated"
        assert result["dog_id"] == 123
        mock_es_service.get_latest_index_for_dog.assert_called_once_with(123)
        mock_es_service.update_dog_document.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_dog_no_index(self, dog_service, mock_es_service):
        """Test dog update when no index is found"""
        dog_update = DogUpdate(name="Updated Name")
        mock_es_service.get_latest_index_for_dog.return_value = None
        
        with pytest.raises(ValueError, match="No index found for dog 123"):
            await dog_service.update_dog(123, dog_update)
    
    @pytest.mark.asyncio
    async def test_get_recent_adoptions(self, dog_service, mock_es_service):
        """Test retrieving recent adoptions"""
        mock_es_service.get_adopted_dogs_this_week.return_value = (
            ["Buddy", "Max"],
            ["2025-01-15T10:00:00+00:00", "2025-01-16T14:30:00+00:00"],
            ["http://example.com/buddy", "http://example.com/max"],
            [30, 45],
            2
        )
        
        result = await dog_service.get_recent_adoptions()
        
        assert len(result) == 2
        assert result[0]["name"] == "Buddy"
        assert result[0]["date"] == "01/15/2025"
        assert result[0]["los"] == 30
        assert result[1]["name"] == "Max"
    
    @pytest.mark.asyncio
    async def test_get_insights(self, dog_service, mock_es_service):
        """Test retrieving insights"""
        mock_daily_adoptions = [
            {"date": "2025-01-15", "count": 3},
            {"date": "2025-01-16", "count": 2}
        ]
        mock_es_service.get_adoptions_per_day.return_value = mock_daily_adoptions
        
        result = await dog_service.get_insights()
        
        assert result["dailyAdoptions"] == mock_daily_adoptions
    
    @pytest.mark.asyncio
    async def test_error_handling(self, dog_service, mock_es_service):
        """Test error handling in service methods"""
        mock_es_service.get_current_listed_count.side_effect = Exception("Database error")
        
        with pytest.raises(Exception, match="Database error"):
            await dog_service.get_overview_stats()

if __name__ == "__main__":
    pytest.main([__file__])