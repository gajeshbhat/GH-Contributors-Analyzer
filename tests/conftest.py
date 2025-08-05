"""
Pytest configuration and fixtures for GitHub Contributors Analyzer tests.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.github_analyzer.github_client import Repository, Contributor
from src.github_analyzer.database import DatabaseHandler


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_github_client():
    """Mock GitHub client for testing."""
    client = MagicMock()
    client.get_repositories_by_topic = AsyncMock()
    client.get_contributors = AsyncMock()
    client.get_trending_repositories = AsyncMock()
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_database_handler():
    """Mock database handler for testing."""
    handler = MagicMock()
    handler.connect = AsyncMock()
    handler.disconnect = AsyncMock()
    handler.save_repository = AsyncMock()
    handler.save_contributors = AsyncMock()
    handler.get_repositories_by_topic = AsyncMock()
    handler.get_top_contributors = AsyncMock()
    handler.get_database_stats = AsyncMock()
    handler.clear_all_data = AsyncMock()
    return handler


@pytest.fixture
def sample_repository():
    """Sample repository data for testing."""
    return Repository(
        id="R_123456789",
        name="test-repo",
        owner="testuser",
        description="A test repository",
        url="https://github.com/testuser/test-repo",
        stargazers_count=100,
        forks_count=20,
        watchers_count=50,
        language="Python",
        topics=["python", "testing"],
        created_at=datetime(2023, 1, 1),
        updated_at=datetime(2023, 12, 1),
        is_fork=False,
        is_archived=False
    )


@pytest.fixture
def sample_contributor():
    """Sample contributor data for testing."""
    return Contributor(
        login="testcontributor",
        id="U_123456789",
        avatar_url="https://avatars.githubusercontent.com/u/123456789",
        html_url="https://github.com/testcontributor",
        contributions=50,
        type="User"
    )


@pytest.fixture
def sample_repositories(sample_repository):
    """List of sample repositories for testing."""
    repos = []
    for i in range(5):
        repo = Repository(
            id=f"R_12345678{i}",
            name=f"test-repo-{i}",
            owner="testuser",
            description=f"Test repository {i}",
            url=f"https://github.com/testuser/test-repo-{i}",
            stargazers_count=100 - i * 10,
            forks_count=20 - i * 2,
            watchers_count=50 - i * 5,
            language="Python",
            topics=["python", "testing"],
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2023, 12, 1),
            is_fork=False,
            is_archived=False
        )
        repos.append(repo)
    return repos


@pytest.fixture
def sample_contributors(sample_contributor):
    """List of sample contributors for testing."""
    contributors = []
    for i in range(3):
        contrib = Contributor(
            login=f"testcontributor{i}",
            id=f"U_12345678{i}",
            avatar_url=f"https://avatars.githubusercontent.com/u/12345678{i}",
            html_url=f"https://github.com/testcontributor{i}",
            contributions=50 - i * 10,
            type="User"
        )
        contributors.append(contrib)
    return contributors
