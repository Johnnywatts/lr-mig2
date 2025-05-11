"""
Tests for database connection module.
"""
import pytest
from src.database import db

def test_database_connection():
    """Test that we can connect to the database."""
    assert db.test_connection() is True

def test_database_cursor():
    """Test that we can create and use a cursor."""
    with db.get_cursor() as cursor:
        cursor.execute('SELECT 1 as test')
        result = cursor.fetchone()
        assert result['test'] == 1 