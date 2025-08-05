"""
Tests for GitHub client functionality.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from src.github_analyzer.github_client import GitHubClient, Repository, Contributor


class TestGitHubClient:
    """Test cases for GitHubClient."""

    @pytest.fixture
    def github_client(self):
        """Create a GitHub client for testing."""
        return GitHubClient("test_token")

    @pytest.mark.asyncio
    async def test_get_repositories_by_topic(self, github_client, sample_repositories):
        """Test fetching repositories by topic."""
        # Mock the GraphQL client
        mock_result = {
            "rateLimit": {
                "limit": 5000,
                "remaining": 4999,
                "resetAt": "2024-01-01T00:00:00Z",
                "used": 1
            },
            "search": {
                "repositoryCount": 5,
                "edges": [
                    {
                        "node": {
                            "id": repo.id,
                            "name": repo.name,
                            "owner": {"login": repo.owner},
                            "description": repo.description,
                            "url": repo.url,
                            "stargazerCount": repo.stargazers_count,
                            "forkCount": repo.forks_count,
                            "watchers": {"totalCount": repo.watchers_count},
                            "primaryLanguage": {"name": repo.language} if repo.language else None,
                            "repositoryTopics": {
                                "edges": [
                                    {"node": {"topic": {"name": topic}}}
                                    for topic in repo.topics
                                ]
                            },
                            "createdAt": repo.created_at.isoformat() + "Z",
                            "updatedAt": repo.updated_at.isoformat() + "Z",
                            "isFork": repo.is_fork,
                            "isArchived": repo.is_archived
                        }
                    }
                    for repo in sample_repositories
                ]
            }
        }

        github_client.client.execute_async = AsyncMock(return_value=mock_result)

        repositories = await github_client.get_repositories_by_topic("python", 5)

        assert len(repositories) == 5
        assert all(isinstance(repo, Repository) for repo in repositories)
        assert repositories[0].name == "test-repo-0"
        assert repositories[0].owner == "testuser"
        assert repositories[0].language == "Python"

    @pytest.mark.asyncio
    async def test_get_contributors(self, github_client, sample_contributors):
        """Test fetching contributors for a repository."""
        mock_response_data = [
            {
                "login": contrib.login,
                "id": int(contrib.id.split("_")[1]),
                "avatar_url": contrib.avatar_url,
                "html_url": contrib.html_url,
                "contributions": contrib.contributions,
                "type": contrib.type
            }
            for contrib in sample_contributors
        ]

        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

            contributors = await github_client.get_contributors("testuser", "test-repo", 3)

            assert len(contributors) == 3
            assert all(isinstance(contrib, Contributor) for contrib in contributors)
            assert contributors[0].login == "testcontributor0"
            assert contributors[0].contributions == 50

    @pytest.mark.asyncio
    async def test_get_trending_repositories(self, github_client, sample_repositories):
        """Test fetching trending repositories."""
        mock_result = {
            "rateLimit": {
                "limit": 5000,
                "remaining": 4999,
                "resetAt": "2024-01-01T00:00:00Z",
                "used": 1
            },
            "search": {
                "repositoryCount": 5,
                "edges": [
                    {
                        "node": {
                            "id": repo.id,
                            "name": repo.name,
                            "owner": {"login": repo.owner},
                            "description": repo.description,
                            "url": repo.url,
                            "stargazerCount": repo.stargazers_count,
                            "forkCount": repo.forks_count,
                            "watchers": {"totalCount": repo.watchers_count},
                            "primaryLanguage": {"name": repo.language} if repo.language else None,
                            "repositoryTopics": {
                                "edges": [
                                    {"node": {"topic": {"name": topic}}}
                                    for topic in repo.topics
                                ]
                            },
                            "createdAt": repo.created_at.isoformat() + "Z",
                            "updatedAt": repo.updated_at.isoformat() + "Z",
                            "isFork": repo.is_fork,
                            "isArchived": repo.is_archived
                        }
                    }
                    for repo in sample_repositories
                ]
            }
        }

        github_client.client.execute_async = AsyncMock(return_value=mock_result)

        repositories = await github_client.get_trending_repositories("python", "daily", 5)

        assert len(repositories) == 5
        assert all(isinstance(repo, Repository) for repo in repositories)

    @pytest.mark.asyncio
    async def test_rate_limiting(self, github_client):
        """Test rate limiting functionality."""
        # Test that rate limiting waits when remaining requests are low
        github_client.rate_limit = MagicMock()
        github_client.rate_limit.remaining = 5
        github_client.rate_limit.reset_at = datetime.now()

        with patch('asyncio.sleep') as mock_sleep:
            await github_client._check_rate_limit()
            # Should not sleep since reset_at is now
            mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_close(self, github_client):
        """Test closing the client."""
        github_client.client.transport.close = AsyncMock()
        
        await github_client.close()
        
        github_client.client.transport.close.assert_called_once()
