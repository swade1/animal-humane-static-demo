"""
MongoDB service for Animal Humane project
"""
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import logging
from config import config

logger = logging.getLogger(__name__)

class MongoDBService:
    def __init__(self):
        # Get connection string from config
        connection_string = config.mongodb.get_connection_string()

        try:
            self.client = MongoClient(connection_string)
            # Test the connection
            self.client.admin.command('ping')
            logger.info("✅ MongoDB connection successful")
        except ConnectionFailure as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ MongoDB authentication failed: {e}")
            raise

    def get_database(self, db_name=None):
        """Get database instance"""
        if db_name is None:
            db_name = config.mongodb.database
        return self.client[db_name]

    def close(self):
        """Close the connection"""
        if self.client:
            self.client.close()