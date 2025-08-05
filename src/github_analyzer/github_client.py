"""
Modern GitHub GraphQL API client with rate limiting and error handling.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

import aiohttp
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
import structlog

from .config import settings

logger = structlog.get_logger(__name__)


@dataclass
class RateLimit:
    """GitHub API rate limit information."""
    limit: int
    remaining: int
    reset_at: datetime
    used: int


@dataclass
class Repository:
    """Repository information from GitHub API."""
    id: str
    name: str
    owner: str
    description: Optional[str]
    url: str
    stargazers_count: int
    forks_count: int
    watchers_count: int
    language: Optional[str]
    topics: List[str]
    created_at: datetime
    updated_at: datetime
    is_fork: bool
    is_archived: bool


@dataclass
class Contributor:
    """Contributor information from GitHub API."""
    login: str
    id: str
    avatar_url: str
    html_url: str
    contributions: int
    type: str


class GitHubClient:
    """Modern GitHub GraphQL API client with rate limiting."""
    
    def __init__(self, token: str):
        """Initialize the GitHub client with authentication."""
        self.token = token
        self.rate_limit: Optional[RateLimit] = None
        self.last_request_time = 0.0
        
        # Setup GraphQL transport with authentication
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "GitHub-Contributors-Analyzer/2.0"
        }
        
        transport = AIOHTTPTransport(
            url=settings.github_api_url,
            headers=headers
        )
        
        self.client = Client(
            transport=transport,
            fetch_schema_from_transport=False
        )
        
        logger.info("GitHub client initialized", api_url=settings.github_api_url)
    
    async def _check_rate_limit(self) -> None:
        """Check and handle rate limiting."""
        if self.rate_limit and self.rate_limit.remaining <= 10:
            wait_time = (self.rate_limit.reset_at - datetime.now()).total_seconds()
            if wait_time > 0:
                logger.warning(
                    "Rate limit nearly exceeded, waiting",
                    remaining=self.rate_limit.remaining,
                    wait_seconds=wait_time
                )
                await asyncio.sleep(wait_time)
        
        # Ensure minimum delay between requests
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_delay = 1.0  # 1 second minimum between requests
        
        if time_since_last < min_delay:
            await asyncio.sleep(min_delay - time_since_last)
        
        self.last_request_time = time.time()
    
    def _update_rate_limit(self, response_data: Dict[str, Any]) -> None:
        """Update rate limit information from response."""
        if "rateLimit" in response_data:
            rate_limit_data = response_data["rateLimit"]
            self.rate_limit = RateLimit(
                limit=rate_limit_data["limit"],
                remaining=rate_limit_data["remaining"],
                reset_at=datetime.fromisoformat(
                    rate_limit_data["resetAt"].replace("Z", "+00:00")
                ),
                used=rate_limit_data["used"]
            )
            
            logger.debug(
                "Rate limit updated",
                remaining=self.rate_limit.remaining,
                reset_at=self.rate_limit.reset_at
            )
    
    async def get_repositories_by_topic(
        self, 
        topic: str, 
        limit: int = 100
    ) -> List[Repository]:
        """Get repositories for a specific topic using GraphQL."""
        await self._check_rate_limit()
        
        query = gql("""
            query GetRepositoriesByTopic($topic: String!, $limit: Int!) {
                rateLimit {
                    limit
                    remaining
                    resetAt
                    used
                }
                search(
                    query: $topic
                    type: REPOSITORY
                    first: $limit
                ) {
                    repositoryCount
                    edges {
                        node {
                            ... on Repository {
                                id
                                name
                                owner {
                                    login
                                }
                                description
                                url
                                stargazerCount
                                forkCount
                                watchers {
                                    totalCount
                                }
                                primaryLanguage {
                                    name
                                }
                                repositoryTopics(first: 20) {
                                    edges {
                                        node {
                                            topic {
                                                name
                                            }
                                        }
                                    }
                                }
                                createdAt
                                updatedAt
                                isFork
                                isArchived
                            }
                        }
                    }
                }
            }
        """)
        
        try:
            variables = {"topic": f"topic:{topic}", "limit": limit}
            result = await self.client.execute_async(query, variable_values=variables)
            
            self._update_rate_limit(result)
            
            repositories = []
            for edge in result["search"]["edges"]:
                repo_data = edge["node"]
                
                topics = [
                    topic_edge["node"]["topic"]["name"]
                    for topic_edge in repo_data["repositoryTopics"]["edges"]
                ]
                
                repository = Repository(
                    id=repo_data["id"],
                    name=repo_data["name"],
                    owner=repo_data["owner"]["login"],
                    description=repo_data.get("description"),
                    url=repo_data["url"],
                    stargazers_count=repo_data["stargazerCount"],
                    forks_count=repo_data["forkCount"],
                    watchers_count=repo_data["watchers"]["totalCount"],
                    language=repo_data["primaryLanguage"]["name"] if repo_data["primaryLanguage"] else None,
                    topics=topics,
                    created_at=datetime.fromisoformat(repo_data["createdAt"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(repo_data["updatedAt"].replace("Z", "+00:00")),
                    is_fork=repo_data["isFork"],
                    is_archived=repo_data["isArchived"]
                )
                repositories.append(repository)
            
            logger.info(
                "Fetched repositories by topic",
                topic=topic,
                count=len(repositories),
                total_available=result["search"]["repositoryCount"]
            )
            
            return repositories
            
        except Exception as e:
            logger.error("Failed to fetch repositories by topic", topic=topic, error=str(e))
            raise

    async def get_contributors(
        self,
        owner: str,
        repo_name: str,
        limit: int = 100
    ) -> List[Contributor]:
        """Get top contributors for a repository using REST API (GraphQL doesn't support contributors)."""
        await self._check_rate_limit()

        # Use REST API for contributors as GraphQL doesn't support this endpoint
        url = f"https://api.github.com/repos/{owner}/{repo_name}/contributors"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-Contributors-Analyzer/2.0"
        }

        try:
            async with aiohttp.ClientSession() as session:
                params = {"per_page": min(limit, 100), "page": 1}
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        contributors_data = await response.json()

                        contributors = []
                        for contrib_data in contributors_data:
                            contributor = Contributor(
                                login=contrib_data["login"],
                                id=str(contrib_data["id"]),
                                avatar_url=contrib_data["avatar_url"],
                                html_url=contrib_data["html_url"],
                                contributions=contrib_data["contributions"],
                                type=contrib_data["type"]
                            )
                            contributors.append(contributor)

                        logger.info(
                            "Fetched contributors",
                            owner=owner,
                            repo=repo_name,
                            count=len(contributors)
                        )

                        return contributors

                    elif response.status == 403:
                        # Handle rate limiting
                        reset_time = response.headers.get("X-RateLimit-Reset")
                        if reset_time:
                            wait_time = int(reset_time) - int(time.time())
                            if wait_time > 0:
                                logger.warning(
                                    "REST API rate limited, waiting",
                                    wait_seconds=wait_time
                                )
                                await asyncio.sleep(wait_time)
                                return await self.get_contributors(owner, repo_name, limit)

                        logger.error("REST API rate limit exceeded", owner=owner, repo=repo_name)
                        return []

                    else:
                        logger.error(
                            "Failed to fetch contributors",
                            owner=owner,
                            repo=repo_name,
                            status=response.status
                        )
                        return []

        except Exception as e:
            logger.error(
                "Error fetching contributors",
                owner=owner,
                repo=repo_name,
                error=str(e)
            )
            return []

    async def get_trending_repositories(
        self,
        language: Optional[str] = None,
        since: str = "daily",
        limit: int = 100
    ) -> List[Repository]:
        """Get trending repositories using search with sorting."""
        await self._check_rate_limit()

        # Build search query for trending repos
        query_parts = []

        if language:
            query_parts.append(f"language:{language}")

        # Get repositories created in the last week for "trending"
        since_date = datetime.now() - timedelta(days=7)
        query_parts.append(f"created:>{since_date.strftime('%Y-%m-%d')}")

        search_query = " ".join(query_parts) if query_parts else "stars:>1"

        query = gql("""
            query GetTrendingRepositories($searchQuery: String!, $limit: Int!) {
                rateLimit {
                    limit
                    remaining
                    resetAt
                    used
                }
                search(
                    query: $searchQuery
                    type: REPOSITORY
                    first: $limit
                ) {
                    repositoryCount
                    edges {
                        node {
                            ... on Repository {
                                id
                                name
                                owner {
                                    login
                                }
                                description
                                url
                                stargazerCount
                                forkCount
                                watchers {
                                    totalCount
                                }
                                primaryLanguage {
                                    name
                                }
                                repositoryTopics(first: 20) {
                                    edges {
                                        node {
                                            topic {
                                                name
                                            }
                                        }
                                    }
                                }
                                createdAt
                                updatedAt
                                isFork
                                isArchived
                            }
                        }
                    }
                }
            }
        """)

        try:
            variables = {"searchQuery": search_query, "limit": limit}
            result = await self.client.execute_async(query, variable_values=variables)

            self._update_rate_limit(result)

            repositories = []
            for edge in result["search"]["edges"]:
                repo_data = edge["node"]

                topics = [
                    topic_edge["node"]["topic"]["name"]
                    for topic_edge in repo_data["repositoryTopics"]["edges"]
                ]

                repository = Repository(
                    id=repo_data["id"],
                    name=repo_data["name"],
                    owner=repo_data["owner"]["login"],
                    description=repo_data.get("description"),
                    url=repo_data["url"],
                    stargazers_count=repo_data["stargazerCount"],
                    forks_count=repo_data["forkCount"],
                    watchers_count=repo_data["watchers"]["totalCount"],
                    language=repo_data["primaryLanguage"]["name"] if repo_data["primaryLanguage"] else None,
                    topics=topics,
                    created_at=datetime.fromisoformat(repo_data["createdAt"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(repo_data["updatedAt"].replace("Z", "+00:00")),
                    is_fork=repo_data["isFork"],
                    is_archived=repo_data["isArchived"]
                )
                repositories.append(repository)

            logger.info(
                "Fetched trending repositories",
                language=language,
                since=since,
                count=len(repositories)
            )

            return repositories

        except Exception as e:
            logger.error("Failed to fetch trending repositories", error=str(e))
            raise

    async def close(self) -> None:
        """Close the client and cleanup resources."""
        await self.client.transport.close()
        logger.info("GitHub client closed")
