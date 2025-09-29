"""
Enhanced Elasticsearch client with connection pooling and retry logic
"""
import time
from typing import Optional, Dict, Any
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, TransportError
from urllib3.util.retry import Retry
from urllib3 import PoolManager

from config import config
from utils.logger import setup_logger

logger = setup_logger("elasticsearch_client")

class ElasticsearchClient:
    _instance: Optional['ElasticsearchClient'] = None
    _client: Optional[Elasticsearch] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self._client = self._create_client()
    
    def _create_client(self) -> Elasticsearch:
        """Create Elasticsearch client with retry logic and connection pooling"""
        retry_strategy = Retry(
            total=config.elasticsearch.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        # Connection pooling configuration
        pool_manager = PoolManager(
            num_pools=10,
            maxsize=20,
            retries=retry_strategy
        )
        
        client = Elasticsearch(
            [config.elasticsearch.host],
            timeout=config.elasticsearch.timeout,
            max_retries=config.elasticsearch.max_retries,
            retry_on_timeout=True,
            # Connection pool settings
            maxsize=25,
            # Health check
            sniff_on_start=True,
            sniff_on_connection_fail=True,
            sniffer_timeout=60,
        )
        
        # Test connection
        try:
            client.ping()
            logger.info("Successfully connected to Elasticsearch")
        except ConnectionError as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            raise
        
        return client
    
    @property
    def client(self) -> Elasticsearch:
        """Get the Elasticsearch client instance"""
        if self._client is None:
            self._client = self._create_client()
        return self._client
    
    def execute_with_retry(self, operation, *args, max_retries: int = 3, **kwargs):
        """Execute an Elasticsearch operation with retry logic"""
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return operation(*args, **kwargs)
            except (ConnectionError, TransportError) as e:
                last_exception = e
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(
                        f"Elasticsearch operation failed (attempt {attempt + 1}/{max_retries + 1}). "
                        f"Retrying in {wait_time} seconds. Error: {e}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Elasticsearch operation failed after {max_retries + 1} attempts")
                    raise last_exception
            except Exception as e:
                logger.error(f"Unexpected error in Elasticsearch operation: {e}")
                raise
        
        raise last_exception
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on Elasticsearch cluster"""
        try:
            cluster_health = self.client.cluster.health()
            return {
                "status": "healthy",
                "cluster_status": cluster_health.get("status"),
                "number_of_nodes": cluster_health.get("number_of_nodes"),
                "active_shards": cluster_health.get("active_shards"),
            }
        except Exception as e:
            logger.error(f"Elasticsearch health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# Global client instance
es_client = ElasticsearchClient()