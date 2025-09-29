"""
Pydantic models for API request/response validation
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator

class DogBase(BaseModel):
    name: str
    id: int
    breed: Optional[str] = None
    secondary_breed: Optional[str] = None
    age_group: Optional[str] = None
    weight_group: Optional[str] = None
    color: Optional[str] = None
    status: str = "Available"
    location: Optional[str] = None
    origin: Optional[str] = None
    intake_date: Optional[str] = None
    length_of_stay_days: Optional[int] = None
    url: Optional[str] = None
    bite_quarantine: int = 0
    returned: int = 0
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class DogResponse(DogBase):
    timestamp: Optional[str] = None
    index: Optional[str] = None

class DogUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    origin: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    age_group: Optional[str] = None
    bite_quarantine: Optional[int] = None
    breed: Optional[str] = None
    secondary_breed: Optional[str] = None
    color: Optional[str] = None
    status: Optional[str] = None
    weight_group: Optional[str] = None
    index: Optional[str] = None

class OverviewStats(BaseModel):
    total: int
    newThisWeek: int
    adoptedThisWeek: int
    trialAdoptions: int
    avgStay: int
    longestStay: Dict[str, Any]
    ageGroups: List[Dict[str, Any]]

class AdoptionRecord(BaseModel):
    name: str
    date: str
    url: str
    los: int

class OriginData(BaseModel):
    origin: str
    latitude: float
    longitude: float
    count: int

class APIResponse(BaseModel):
    success: bool = True
    data: Optional[Any] = None
    message: Optional[str] = None
    error: Optional[str] = None

    @classmethod
    def success_response(cls, data: Any = None, message: str = None):
        return cls(success=True, data=data, message=message)
    
    @classmethod
    def error_response(cls, error: str, data: Any = None):
        return cls(success=False, error=error, data=data)