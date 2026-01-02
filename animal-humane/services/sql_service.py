"""
SQL Service for caching API responses
Provides database connection management and CRUD operations for cached data
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SQLService:
    def __init__(self):
        self.connection_string = os.getenv('DATABASE_URL')
        if not self.connection_string:
            raise ValueError("DATABASE_URL environment variable not set")

    def get_connection(self):
        """Create a new database connection"""
        return psycopg2.connect(self.connection_string, cursor_factory=RealDictCursor)

    def insert_overview_stats(self, overview_data: Dict[str, Any]) -> bool:
        """Insert overview statistics into the database"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Extract data from the overview response
                    total_dogs = overview_data.get('total_dogs', 0)
                    new_this_week = overview_data.get('new_this_week', 0)
                    adopted_this_week = overview_data.get('adopted_this_week', 0)
                    trial_adoptions = overview_data.get('trial_adoptions', 0)
                    
                    # Extract age group counts
                    age_groups = overview_data.get('available_dogs_by_age_group', {})
                    puppies_count = age_groups.get('puppies', 0)
                    adults_count = age_groups.get('adults', 0)
                    seniors_count = age_groups.get('seniors', 0)
                    
                    # Extract longest resident info
                    longest_resident = overview_data.get('longest_resident', {})
                    longest_resident_name = longest_resident.get('name')
                    longest_resident_days = longest_resident.get('days')
                    longest_resident_url = longest_resident.get('url')
                    
                    # Insert the data
                    cursor.execute("""
                        INSERT INTO overview_stats (
                            total_dogs, new_this_week, adopted_this_week, trial_adoptions,
                            puppies_count, adults_count, seniors_count,
                            longest_resident_name, longest_resident_days, longest_resident_url
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        total_dogs, new_this_week, adopted_this_week, trial_adoptions,
                        puppies_count, adults_count, seniors_count,
                        longest_resident_name, longest_resident_days, longest_resident_url
                    ))
                    
                    conn.commit()
                    logger.info("Successfully inserted overview stats into SQL database")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to insert overview stats into SQL database: {e}")
            return False

    def get_overview_stats(self) -> Optional[Dict[str, Any]]:
        """Get the most recent overview statistics from SQL database"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get the most recent record
                    cursor.execute("""
                        SELECT * FROM overview_stats 
                        ORDER BY updated_at DESC 
                        LIMIT 1
                    """)
                    
                    result = cursor.fetchone()
                    if result:
                        # Convert to the expected API format
                        return {
                            'total_dogs': result['total_dogs'],
                            'new_this_week': result['new_this_week'],
                            'adopted_this_week': result['adopted_this_week'],
                            'trial_adoptions': result['trial_adoptions'],
                            'available_dogs_by_age_group': {
                                'puppies': result['puppies_count'],
                                'adults': result['adults_count'],
                                'seniors': result['seniors_count']
                            },
                            'longest_resident': {
                                'name': result['longest_resident_name'],
                                'days': result['longest_resident_days'],
                                'url': result['longest_resident_url']
                            }
                        }
                    
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to get overview stats from SQL database: {e}")
            return None
