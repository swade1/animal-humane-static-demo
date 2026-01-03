"""
Configuration management for Animal Humane project
"""
import os
from dataclasses import dataclass
from typing import Dict, Any

print("--------------------------------------------LOADING config.py from", __file__)

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
    internal_auth_token: str = None

    def __post_init__(self):
        print("+++++++++++++++++++++++++++++++++++++APIConfig loaded, internal_auth_token:", getattr(self, "internal_auth_token", "NOT SET"))
        if self.cors_origins is None:
            self.cors_origins = ["http://localhost:3000"]
        # Optional internal auth token for scheduler/API internal calls
        self.internal_auth_token = os.getenv('INTERNAL_API_TOKEN') or None

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
        elasticsearch_host = os.getenv("ELASTICSEARCH_HOST")
        es_host = os.getenv("ES_HOST")
        print(f"DEBUG: ELASTICSEARCH_HOST={elasticsearch_host}")
        print(f"DEBUG: ES_HOST={es_host}")
        
        if elasticsearch_host:
            print(f"DEBUG: Setting elasticsearch.host to {elasticsearch_host}")
            self.elasticsearch.host = elasticsearch_host
        elif es_host:
            print(f"DEBUG: Setting elasticsearch.host to {es_host}")
            self.elasticsearch.host = es_host
        else:
            print(f"DEBUG: No env vars found, using default: {self.elasticsearch.host}")
            
        if os.getenv("API_PORT"):
            self.api.port = int(os.getenv("API_PORT"))
        if os.getenv("DEBUG"):
            self.api.debug = os.getenv("DEBUG").lower() == "true"

# Global config instance
config = Config()
