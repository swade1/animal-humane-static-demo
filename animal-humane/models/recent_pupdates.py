#!/usr/bin/env python3
"""
Data models and contracts for Recent Pupdates functionality
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum


class PupdateSection(str, Enum):
    """Enumeration of available pupdate sections"""
    NEW_DOGS = "new_dogs"
    RETURNED_DOGS = "returned_dogs"
    ADOPTED_DOGS = "adopted_dogs"
    TRIAL_DOGS = "trial_dogs"
    UNLISTED_DOGS = "unlisted_dogs"
    AVAILABLE_SOON = "available_soon"


@dataclass
class DogEntry:
    """Standardized dog entry for all sections"""
    id: int
    name: str
    url: str
    status: Optional[str] = None
    location: Optional[str] = None
    section_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Ensure URL is properly formatted"""
        if self.url and not self.url.startswith('http'):
            self.url = f"https://new.shelterluv.com/embed/animal/{self.id}"


@dataclass
class SectionConfig:
    """Configuration for pupdate sections"""
    name: str
    title: str
    description: str
    data_source: str
    exclusions: List[str] = field(default_factory=list)  # Other sections to exclude from
    enabled: bool = True


@dataclass
class DataFreshness:
    """Data freshness indicators"""
    elasticsearch_last_update: Optional[datetime] = None
    missing_dogs_last_update: Optional[datetime] = None
    analysis_timestamp: Optional[datetime] = None
    cache_timestamp: Optional[datetime] = None


@dataclass
class RecentPupdatesData:
    """Unified data structure for all Recent Pupdates sections"""
    new_dogs: List[DogEntry] = field(default_factory=list)
    returned_dogs: List[DogEntry] = field(default_factory=list)
    adopted_dogs: List[DogEntry] = field(default_factory=list)
    trial_dogs: List[DogEntry] = field(default_factory=list)
    unlisted_dogs: List[DogEntry] = field(default_factory=list)
    available_soon: List[DogEntry] = field(default_factory=list)
    
    last_updated: datetime = field(default_factory=datetime.now)
    data_freshness: DataFreshness = field(default_factory=DataFreshness)
    section_configs: Dict[str, SectionConfig] = field(default_factory=dict)
    
    # Statistics and metadata
    total_dogs: int = 0
    data_quality_score: float = 1.0
    warnings: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Calculate derived fields"""
        all_sections = [
            self.new_dogs, self.returned_dogs, self.adopted_dogs,
            self.trial_dogs, self.unlisted_dogs, self.available_soon
        ]
        self.total_dogs = sum(len(section) for section in all_sections)


# Default section configurations
DEFAULT_SECTION_CONFIGS = {
    PupdateSection.NEW_DOGS.value: SectionConfig(
        name=PupdateSection.NEW_DOGS.value,
        title="New Dogs",
        description="Dogs that have recently arrived and are now available for adoption",
        data_source="diff_analysis.new_dogs",
        exclusions=[PupdateSection.AVAILABLE_SOON.value]
    ),
    PupdateSection.RETURNED_DOGS.value: SectionConfig(
        name=PupdateSection.RETURNED_DOGS.value,
        title="Returned Dogs", 
        description="Dogs that have returned from previous adoptions or placements",
        data_source="diff_analysis.returned_dogs",
        exclusions=[PupdateSection.AVAILABLE_SOON.value]
    ),
    PupdateSection.ADOPTED_DOGS.value: SectionConfig(
        name=PupdateSection.ADOPTED_DOGS.value,
        title="Adopted/Reclaimed Dogs",
        description="Dogs that have been successfully adopted or reclaimed",
        data_source="diff_analysis.adopted_dogs",
        exclusions=[PupdateSection.AVAILABLE_SOON.value]
    ),
    PupdateSection.TRIAL_DOGS.value: SectionConfig(
        name=PupdateSection.TRIAL_DOGS.value,
        title="Trial Adoptions",
        description="Dogs currently in trial adoption periods", 
        data_source="diff_analysis.trial_adoption_dogs",
        exclusions=[PupdateSection.AVAILABLE_SOON.value]
    ),
    PupdateSection.UNLISTED_DOGS.value: SectionConfig(
        name=PupdateSection.UNLISTED_DOGS.value,
        title="Available but Temporarily Unlisted",
        description="Dogs that are available but temporarily not listed on the website",
        data_source="diff_analysis.other_unlisted_dogs", 
        exclusions=[PupdateSection.NEW_DOGS.value, PupdateSection.AVAILABLE_SOON.value]
    ),
    PupdateSection.AVAILABLE_SOON.value: SectionConfig(
        name=PupdateSection.AVAILABLE_SOON.value,
        title="Available Soon",
        description="Dogs at the shelter but not yet listed on the website",
        data_source="missing_dogs",
        exclusions=[PupdateSection.NEW_DOGS.value]  # Only exclude New Dogs for mutual exclusivity
    )
}