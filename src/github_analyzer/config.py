"""
Configuration management using Pydantic settings.
"""

from typing import Optional
from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # GitHub API Configuration
    github_token: Optional[str] = Field(default=None, description="GitHub Personal Access Token")
    github_api_url: str = Field(
        default="https://api.github.com/graphql",
        description="GitHub GraphQL API URL"
    )
    
    # MongoDB Configuration
    mongodb_uri: str = Field(
        default="mongodb://localhost:27017/",
        description="MongoDB connection URI"
    )
    mongodb_database: str = Field(
        default="github_contributors",
        description="MongoDB database name"
    )
    mongodb_collection: str = Field(
        default="repositories",
        description="MongoDB collection name"
    )
    
    # Application Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    max_repositories_per_topic: int = Field(
        default=100,
        description="Maximum repositories to fetch per topic"
    )
    max_contributors_per_repo: int = Field(
        default=100,
        description="Maximum contributors to fetch per repository"
    )
    rate_limit_requests_per_hour: int = Field(
        default=5000,
        description="GitHub API rate limit per hour"
    )

    @field_validator('max_repositories_per_topic')
    @classmethod
    def validate_max_repositories(cls, v):
        if v <= 0:
            raise ValueError('max_repositories_per_topic must be greater than 0')
        return v

    @field_validator('max_contributors_per_repo')
    @classmethod
    def validate_max_contributors(cls, v):
        if v <= 0:
            raise ValueError('max_contributors_per_repo must be greater than 0')
        return v

    @field_validator('rate_limit_requests_per_hour')
    @classmethod
    def validate_rate_limit(cls, v):
        if v <= 0:
            raise ValueError('rate_limit_requests_per_hour must be greater than 0')
        return v

    # Docker Configuration
    mongo_initdb_root_username: Optional[str] = Field(
        default=None,
        description="MongoDB root username for Docker"
    )
    mongo_initdb_root_password: Optional[str] = Field(
        default=None,
        description="MongoDB root password for Docker"
    )
    mongo_initdb_database: Optional[str] = Field(
        default=None,
        description="MongoDB initial database for Docker"
    )
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Global settings instance
settings = Settings()
