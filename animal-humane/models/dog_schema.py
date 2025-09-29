"""
Data validation and schema definitions for dog records
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

class AgeGroup(str, Enum):
    PUPPY = "Puppy"
    ADULT = "Adult"
    SENIOR = "Senior"

class WeightGroup(str, Enum):
    SMALL = "Small (0-24)"
    MEDIUM = "Medium (25-59)"
    LARGE = "Large (60-99)"
    EXTRA_LARGE = "Extra-Large (100+)"

class DogStatus(str, Enum):
    AVAILABLE = "Available"
    ADOPTED = "adopted"
    TRIAL_ADOPTION = "Trial Adoption"
    MEDICAL_HOLD = "Medical Hold"
    BEHAVIORAL_HOLD = "Behavioral Hold"

class DogRecord(BaseModel):
    """Complete dog record with validation"""
    id: int = Field(..., description="Unique dog ID")
    name: str = Field(..., min_length=1, max_length=100, description="Dog name")
    status: DogStatus = Field(default=DogStatus.AVAILABLE, description="Current status")
    url: Optional[str] = Field(None, description="Shelter website URL")
    
    # Physical characteristics
    breed: Optional[str] = Field(None, max_length=100, description="Primary breed")
    secondary_breed: Optional[str] = Field(None, max_length=100, description="Secondary breed")
    age_group: Optional[AgeGroup] = Field(None, description="Age category")
    weight_group: Optional[WeightGroup] = Field(None, description="Weight category")
    color: Optional[str] = Field(None, max_length=100, description="Color description")
    
    # Dates
    intake_date: Optional[str] = Field(None, description="Intake date (ISO format)")
    birthdate: Optional[str] = Field(None, description="Birth date (ISO format)")
    timestamp: Optional[str] = Field(None, description="Record timestamp")
    
    # Location and origin
    location: Optional[str] = Field(None, max_length=200, description="Current location")
    origin: Optional[str] = Field(None, max_length=200, description="Origin shelter/source")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Origin latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Origin longitude")
    
    # Behavioral and medical flags
    bite_quarantine: int = Field(default=0, ge=0, description="Bite quarantine count")
    returned: int = Field(default=0, ge=0, description="Return count")
    length_of_stay_days: Optional[int] = Field(None, ge=0, description="Days at shelter")
    
    @validator('intake_date', 'birthdate', 'timestamp', pre=True)
    def validate_date_format(cls, v):
        """Validate date strings are in proper ISO format"""
        if v is None:
            return v
        
        if isinstance(v, str):
            try:
                # Try to parse the date to validate format
                datetime.fromisoformat(v.replace('Z', '+00:00'))
                return v
            except ValueError:
                raise ValueError(f"Invalid date format: {v}. Expected ISO format.")
        
        return v
    
    @validator('url')
    def validate_url(cls, v):
        """Validate URL format"""
        if v is None:
            return v
        
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        
        return v
    
    @validator('name')
    def validate_name(cls, v):
        """Validate and clean dog name"""
        if v:
            # Remove extra whitespace and capitalize properly
            return ' '.join(word.capitalize() for word in v.strip().split())
        return v
    
    class Config:
        use_enum_values = True
        validate_assignment = True

class DogSearchFilters(BaseModel):
    """Filters for dog search operations"""
    status: Optional[List[DogStatus]] = None
    age_group: Optional[List[AgeGroup]] = None
    weight_group: Optional[List[WeightGroup]] = None
    origin: Optional[List[str]] = None
    location: Optional[str] = None
    min_length_of_stay: Optional[int] = Field(None, ge=0)
    max_length_of_stay: Optional[int] = Field(None, ge=0)
    has_bite_quarantine: Optional[bool] = None
    has_returns: Optional[bool] = None
    
    @validator('max_length_of_stay')
    def validate_length_of_stay_range(cls, v, values):
        """Ensure max is greater than min"""
        if v is not None and 'min_length_of_stay' in values:
            min_val = values['min_length_of_stay']
            if min_val is not None and v < min_val:
                raise ValueError('max_length_of_stay must be greater than min_length_of_stay')
        return v

# Elasticsearch mapping for dog records
DOG_INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "status": {"type": "keyword"},
            "url": {"type": "keyword"},
            "breed": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "secondary_breed": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "age_group": {"type": "keyword"},
            "weight_group": {"type": "keyword"},
            "color": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "intake_date": {"type": "date"},
            "birthdate": {"type": "date"},
            "timestamp": {"type": "date"},
            "location": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "origin": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "latitude": {"type": "float"},
            "longitude": {"type": "float"},
            "bite_quarantine": {"type": "integer"},
            "returned": {"type": "integer"},
            "length_of_stay_days": {"type": "integer"}
        }
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 1,
        "refresh_interval": "30s"
    }
}