"""
Tests for configuration management.
"""

import pytest
from unittest.mock import patch, MagicMock
import os

from src.github_analyzer.config import Settings


class TestConfig:
    """Test cases for configuration management."""

    def test_settings_with_env_vars(self):
        """Test settings loading with environment variables."""
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_token_123',
            'MONGODB_URI': 'mongodb://test:27017/',
            'MONGODB_DATABASE': 'test_db',
            'LOG_LEVEL': 'DEBUG',
            'MAX_REPOSITORIES_PER_TOPIC': '200',
            'RATE_LIMIT_REQUESTS_PER_HOUR': '6000'
        }):
            settings = Settings()
            
            assert settings.github_token == 'test_token_123'
            assert settings.mongodb_uri == 'mongodb://test:27017/'
            assert settings.mongodb_database == 'test_db'
            assert settings.log_level == 'DEBUG'
            assert settings.max_repositories_per_topic == 200
            assert settings.rate_limit_requests_per_hour == 6000

    def test_settings_defaults(self):
        """Test settings with default values."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            
            assert settings.github_api_url == 'https://api.github.com/graphql'
            assert settings.mongodb_uri == 'mongodb://localhost:27017/'
            assert settings.mongodb_database == 'github_contributors'
            assert settings.mongodb_collection == 'repositories'
            assert settings.log_level == 'INFO'
            assert settings.max_repositories_per_topic == 100
            assert settings.max_contributors_per_repo == 100
            assert settings.rate_limit_requests_per_hour == 5000

    def test_settings_validation(self):
        """Test settings validation."""
        with patch.dict(os.environ, {
            'MAX_REPOSITORIES_PER_TOPIC': '0',  # Should be > 0
        }):
            with pytest.raises(ValueError):
                Settings()

    def test_github_token_required_for_api_calls(self):
        """Test that GitHub token is properly handled."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            # Token should be None if not provided
            assert settings.github_token is None

        with patch.dict(os.environ, {'GITHUB_TOKEN': 'valid_token'}):
            settings = Settings()
            assert settings.github_token == 'valid_token'
