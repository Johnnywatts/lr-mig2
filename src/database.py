"""
Database connection and operations module for Lightroom File Management Utility.
Handles PostgreSQL connection and basic database operations.
"""
import os
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

class DatabaseConnection:
    """Handles database connection and operations."""
    
    def __init__(self):
        """Initialize database connection parameters."""
        self.db_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'dbname': os.getenv('DB_NAME', 'lrmig2'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', '')
        }
    
    @contextmanager
    def get_connection(self):
        """Create a database connection context manager.
        
        Yields:
            psycopg2.connection: Database connection object
        """
        conn = None
        try:
            conn = psycopg2.connect(**self.db_params)
            yield conn
        finally:
            if conn is not None:
                conn.close()
    
    @contextmanager
    def get_cursor(self, cursor_factory=RealDictCursor):
        """Create a database cursor context manager.
        
        Args:
            cursor_factory: The cursor factory to use (default: RealDictCursor)
            
        Yields:
            psycopg2.cursor: Database cursor object
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                cursor.close()
    
    def test_connection(self) -> bool:
        """Test the database connection.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute('SELECT 1')
                    return True
        except Exception as e:
            print(f"Database connection test failed: {e}")
            return False

# Create a singleton instance
db = DatabaseConnection() 