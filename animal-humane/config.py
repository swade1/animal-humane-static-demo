"""
Configuration management for Animal Humane project
"""
import os
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ElasticsearchConfig:
    host: str = "http://localhost:9200"
    timeout: int = 60
    max_retries: int = 3

@dataclass
class APIConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors_origins: list = None

    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["http://localhost:3000"]

@dataclass
class ScrapingConfig:
    main_url: str = "https://animalhumanenm.org/adopt/adoptable-dogs/"
    request_timeout: int = 30
    retry_attempts: int = 3

class Config:
    def __init__(self):
        self.elasticsearch = ElasticsearchConfig()
        self.api = APIConfig()
        self.scraping = ScrapingConfig()
        
        # Override with environment variables if present
        self._load_from_env()
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        if os.getenv("ES_HOST"):
            self.elasticsearch.host = os.getenv("ES_HOST")
        if os.getenv("API_PORT"):
            self.api.port = int(os.getenv("API_PORT"))
        if os.getenv("DEBUG"):
            self.api.debug = os.getenv("DEBUG").lower() == "true"

# Global config instance
config = Config()