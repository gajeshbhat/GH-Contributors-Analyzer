"""
Modern MongoDB database handler with async support and best practices.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError, ConnectionFailure
import structlog

from .config import settings
from .github_client import Repository, Contributor

logger = structlog.get_logger(__name__)


class DatabaseHandler:
    """Modern async MongoDB handler with connection pooling and error handling."""
    
    def __init__(self):
        """Initialize the database handler."""
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.repositories: Optional[AsyncIOMotorCollection] = None
        self.contributors: Optional[AsyncIOMotorCollection] = None
        self.topics: Optional[AsyncIOMotorCollection] = None
        
    async def connect(self) -> None:
        """Connect to MongoDB with proper error handling."""
        try:
            self.client = AsyncIOMotorClient(
                settings.mongodb_uri,
                maxPoolSize=50,
                minPoolSize=10,
                maxIdleTimeMS=30000,
                waitQueueTimeoutMS=5000,
                serverSelectionTimeoutMS=5000
            )
            
            # Test the connection
            await self.client.admin.command('ping')
            
            self.database = self.client[settings.mongodb_database]
            self.repositories = self.database.repositories
            self.contributors = self.database.contributors
            self.topics = self.database.topics
            
            # Ensure indexes exist
            await self._create_indexes()
            
            logger.info(
                "Connected to MongoDB",
                database=settings.mongodb_database,
                uri=settings.mongodb_uri.split('@')[-1] if '@' in settings.mongodb_uri else settings.mongodb_uri
            )
            
        except ConnectionFailure as e:
            logger.error("Failed to connect to MongoDB", error=str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error connecting to MongoDB", error=str(e))
            raise
    
    async def _create_indexes(self) -> None:
        """Create database indexes for optimal performance."""
        try:
            # Repository indexes
            await self.repositories.create_index([("name", 1), ("owner", 1)], unique=True)
            await self.repositories.create_index([("topics", 1)])
            await self.repositories.create_index([("stargazers_count", -1)])
            await self.repositories.create_index([("created_at", -1)])
            await self.repositories.create_index([("updated_at", -1)])
            await self.repositories.create_index([("language", 1)])
            
            # Contributor indexes
            await self.contributors.create_index([("repository_id", 1), ("login", 1)], unique=True)
            await self.contributors.create_index([("contributions", -1)])
            await self.contributors.create_index([("login", 1)])
            await self.contributors.create_index([("repository_owner", 1), ("repository_name", 1)])
            
            # Topic indexes
            await self.topics.create_index([("name", 1)], unique=True)
            await self.topics.create_index([("repository_count", -1)])
            await self.topics.create_index([("last_updated", -1)])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.warning("Failed to create some indexes", error=str(e))
    
    async def disconnect(self) -> None:
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    @asynccontextmanager
    async def get_session(self):
        """Get a database session for transactions."""
        async with await self.client.start_session() as session:
            yield session
    
    async def save_repository(self, repository: Repository) -> bool:
        """Save a repository to the database."""
        try:
            repo_doc = {
                "id": repository.id,
                "name": repository.name,
                "owner": repository.owner,
                "description": repository.description,
                "url": repository.url,
                "stargazers_count": repository.stargazers_count,
                "forks_count": repository.forks_count,
                "watchers_count": repository.watchers_count,
                "language": repository.language,
                "topics": repository.topics,
                "created_at": repository.created_at,
                "updated_at": repository.updated_at,
                "is_fork": repository.is_fork,
                "is_archived": repository.is_archived,
                "last_analyzed": datetime.utcnow()
            }
            
            # Use upsert to update existing repositories
            result = await self.repositories.replace_one(
                {"name": repository.name, "owner": repository.owner},
                repo_doc,
                upsert=True
            )
            
            if result.upserted_id:
                logger.debug("Repository inserted", repo=f"{repository.owner}/{repository.name}")
            else:
                logger.debug("Repository updated", repo=f"{repository.owner}/{repository.name}")
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to save repository",
                repo=f"{repository.owner}/{repository.name}",
                error=str(e)
            )
            return False
    
    async def save_contributors(
        self, 
        repository: Repository, 
        contributors: List[Contributor]
    ) -> int:
        """Save contributors for a repository."""
        saved_count = 0
        
        try:
            # Remove existing contributors for this repository
            await self.contributors.delete_many({
                "repository_owner": repository.owner,
                "repository_name": repository.name
            })
            
            # Insert new contributors
            contributor_docs = []
            for contributor in contributors:
                contrib_doc = {
                    "repository_id": repository.id,
                    "repository_owner": repository.owner,
                    "repository_name": repository.name,
                    "login": contributor.login,
                    "id": contributor.id,
                    "avatar_url": contributor.avatar_url,
                    "html_url": contributor.html_url,
                    "contributions": contributor.contributions,
                    "type": contributor.type,
                    "last_updated": datetime.utcnow()
                }
                contributor_docs.append(contrib_doc)
            
            if contributor_docs:
                result = await self.contributors.insert_many(contributor_docs)
                saved_count = len(result.inserted_ids)
                
                logger.debug(
                    "Contributors saved",
                    repo=f"{repository.owner}/{repository.name}",
                    count=saved_count
                )
            
        except Exception as e:
            logger.error(
                "Failed to save contributors",
                repo=f"{repository.owner}/{repository.name}",
                error=str(e)
            )
        
        return saved_count
    
    async def update_topic_stats(self, topic_name: str) -> None:
        """Update statistics for a topic."""
        try:
            # Count repositories with this topic
            repo_count = await self.repositories.count_documents({"topics": topic_name})
            
            # Update or insert topic document
            await self.topics.replace_one(
                {"name": topic_name},
                {
                    "name": topic_name,
                    "repository_count": repo_count,
                    "last_updated": datetime.utcnow()
                },
                upsert=True
            )
            
            logger.debug("Topic stats updated", topic=topic_name, repo_count=repo_count)
            
        except Exception as e:
            logger.error("Failed to update topic stats", topic=topic_name, error=str(e))
    
    async def get_repositories_by_topic(
        self, 
        topic: str, 
        limit: int = 100,
        sort_by: str = "stargazers_count"
    ) -> List[Dict[str, Any]]:
        """Get repositories by topic from database."""
        try:
            cursor = self.repositories.find(
                {"topics": topic}
            ).sort(sort_by, -1).limit(limit)
            
            repositories = await cursor.to_list(length=limit)
            
            logger.debug("Retrieved repositories by topic", topic=topic, count=len(repositories))
            return repositories
            
        except Exception as e:
            logger.error("Failed to get repositories by topic", topic=topic, error=str(e))
            return []
    
    async def get_top_contributors(
        self, 
        repository_owner: str, 
        repository_name: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get top contributors for a repository."""
        try:
            cursor = self.contributors.find({
                "repository_owner": repository_owner,
                "repository_name": repository_name
            }).sort("contributions", -1).limit(limit)
            
            contributors = await cursor.to_list(length=limit)
            
            logger.debug(
                "Retrieved contributors",
                repo=f"{repository_owner}/{repository_name}",
                count=len(contributors)
            )
            return contributors
            
        except Exception as e:
            logger.error(
                "Failed to get contributors",
                repo=f"{repository_owner}/{repository_name}",
                error=str(e)
            )
            return []
    
    async def clear_all_data(self) -> None:
        """Clear all data from the database (use with caution)."""
        try:
            await self.repositories.delete_many({})
            await self.contributors.delete_many({})
            await self.topics.delete_many({})
            
            logger.warning("All database data cleared")
            
        except Exception as e:
            logger.error("Failed to clear database", error=str(e))
            raise
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            repo_count = await self.repositories.count_documents({})
            contributor_count = await self.contributors.count_documents({})
            topic_count = await self.topics.count_documents({})
            
            # Get top languages
            pipeline = [
                {"$match": {"language": {"$ne": None}}},
                {"$group": {"_id": "$language", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            top_languages = await self.repositories.aggregate(pipeline).to_list(length=10)
            
            return {
                "repositories": repo_count,
                "contributors": contributor_count,
                "topics": topic_count,
                "top_languages": top_languages
            }
            
        except Exception as e:
            logger.error("Failed to get database stats", error=str(e))
            return {}
