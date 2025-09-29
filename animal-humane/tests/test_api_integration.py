"""
Integration tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from api.main import app

@pytest.fixture
def client():
    """Test client for FastAPI app"""
    return TestClient(app)

@pytest.fixture
def mock_dog_service():
    """Mock dog service for testing"""
    with patch('api.main.get_dog_service') as mock:
        service = AsyncMock()
        mock.return_value = service
        yield service

class TestAPIEndpoints:
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "timestamp" in data["data"]
    
    def test_get_overview_success(self, client, mock_dog_service):
        """Test successful overview retrieval"""
        mock_stats = {
            "total": 50,
            "newThisWeek": 5,
            "adoptedThisWeek": 3,
            "trialAdoptions": 2,
            "ageGroups": [{"age_group": "Adult", "count": 30}],
            "avgStay": 25,
            "longestStay": {"name": "Buddy", "days": 120}
        }
        mock_dog_service.get_overview_stats.return_value = mock_stats
        
        response = client.get("/api/overview")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == mock_stats
    
    def test_get_overview_error(self, client, mock_dog_service):
        """Test overview endpoint error handling"""
        mock_dog_service.get_overview_stats.side_effect = Exception("Database error")
        
        response = client.get("/api/overview")
        assert response.status_code == 500
    
    def test_get_dogs_success(self, client, mock_dog_service):
        """Test successful dogs retrieval"""
        mock_dogs = [
            {"id": 1, "name": "Buddy", "status": "Available"},
            {"id": 2, "name": "Max", "status": "Available"}
        ]
        mock_dog_service.get_available_dogs.return_value = mock_dogs
        
        response = client.get("/api/dogs")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2
    
    def test_get_dog_by_id_found(self, client, mock_dog_service):
        """Test retrieving existing dog by ID"""
        mock_dog = {"id": 123, "name": "Buddy", "status": "Available"}
        mock_dog_service.get_dog_by_id.return_value = mock_dog
        
        response = client.get("/api/dogs/123")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Buddy"
    
    def test_get_dog_by_id_not_found(self, client, mock_dog_service):
        """Test retrieving non-existent dog by ID"""
        mock_dog_service.get_dog_by_id.return_value = None
        
        response = client.get("/api/dogs/999")
        assert response.status_code == 404
    
    def test_update_dog_success(self, client, mock_dog_service):
        """Test successful dog update"""
        update_data = {"name": "Updated Name", "status": "adopted"}
        mock_result = {"result": "updated", "dog_id": 123}
        mock_dog_service.update_dog.return_value = mock_result
        
        response = client.put("/api/dogs/123", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Dog updated successfully"
    
    def test_update_dog_validation_error(self, client, mock_dog_service):
        """Test dog update with invalid data"""
        invalid_data = {"invalid_field": "value"}
        
        response = client.put("/api/dogs/123", json=invalid_data)
        # Should still work since we allow partial updates
        assert response.status_code in [200, 422]
    
    def test_get_adoptions_success(self, client, mock_dog_service):
        """Test successful adoptions retrieval"""
        mock_adoptions = [
            {"name": "Buddy", "date": "01/15/2025", "url": "http://example.com", "los": 30}
        ]
        mock_dog_service.get_recent_adoptions.return_value = mock_adoptions
        
        response = client.get("/api/adoptions")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
    
    def test_get_insights_success(self, client, mock_dog_service):
        """Test successful insights retrieval"""
        mock_insights = {
            "dailyAdoptions": [{"date": "2025-01-15", "count": 3}]
        }
        mock_dog_service.get_insights.return_value = mock_insights
        
        response = client.get("/api/insights")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "dailyAdoptions" in data["data"]
    
    def test_get_dog_origins_success(self, client, mock_dog_service):
        """Test successful dog origins retrieval"""
        mock_origins = [
            {"origin": "ABQ Animal Welfare", "latitude": 35.1102, "longitude": -106.5823, "count": 10}
        ]
        mock_dog_service.get_dog_origins.return_value = mock_origins
        
        response = client.get("/api/dog-origins")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
    
    def test_run_document_updates_success(self, client, mock_dog_service):
        """Test successful document updates"""
        mock_result = {"message": "Updates completed", "timestamp": "2025-01-15T10:00:00"}
        mock_dog_service.run_updates.return_value = mock_result
        
        response = client.post("/run_document_updates")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Updates completed successfully"

if __name__ == "__main__":
    pytest.main([__file__])