"""
Pytest configuration and fixtures for Real Electricity Price tests.
"""
import sys
import os
from unittest.mock import AsyncMock, Mock
import pytest

# Add the custom component to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'real_electricity_price'))

# Import all config flow validation functions and exceptions  
try:
    import config_flow
except ImportError:
    # Alternative import for pytest
    import sys
    import os
    
    # Make relative imports work
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    comp_dir = os.path.join(parent_dir, 'custom_components', 'real_electricity_price')
    sys.path.insert(0, comp_dir)
    
    import config_flow


@pytest.fixture
def validate_input_api():
    """Fixture providing access to validation API and exceptions."""
    return config_flow


@pytest.fixture  
def mock_hass():
    """Mock Home Assistant instance."""
    return Mock()


@pytest.fixture
def mock_api_client():
    """Mock API client for testing."""
    client = AsyncMock()
    client.get_data = AsyncMock()
    return client