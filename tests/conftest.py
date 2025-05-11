"""
Pytest configuration and fixtures
"""
import pytest
from pathlib import Path

@pytest.fixture
def test_data_dir():
    """Return the path to the test data directory"""
    return Path(__file__).parent / "test_data" 