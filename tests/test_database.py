"""
Tests for database connection module.
"""
import pytest
from src.database import db
from src.logger import setup_logging

# Set up logging
logger = setup_logging()

def test_database_connection():
    """Test that we can connect to the database."""
    logger.info("Testing database connection...")
    result = db.test_connection()
    logger.info(f"Connection test result: {result}")
    assert result is True

def test_database_cursor():
    """Test that we can create and use a cursor."""
    logger.info("Testing database cursor...")
    with db.get_cursor() as cursor:
        cursor.execute('SELECT 1 as test')
        result = cursor.fetchone()
        logger.info(f"Cursor test result: {result}")
        assert result['test'] == 1 