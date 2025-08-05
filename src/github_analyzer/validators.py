"""
Input validation utilities for GitHub Contributors Analyzer.
"""

import re
from typing import List, Optional
from urllib.parse import urlparse

from .exceptions import ValidationError


def validate_github_token(token: str) -> str:
    """
    Validate GitHub personal access token format.
    
    Args:
        token: GitHub token to validate
        
    Returns:
        The validated token
        
    Raises:
        ValidationError: If token format is invalid
    """
    if not token:
        raise ValidationError("GitHub token cannot be empty")
    
    # GitHub tokens are typically 40 characters (classic) or start with ghp_ (fine-grained)
    if len(token) < 20:
        raise ValidationError("GitHub token appears to be too short")
    
    # Check for common token patterns
    if not (token.startswith('ghp_') or token.startswith('github_pat_') or re.match(r'^[a-f0-9]{40}$', token)):
        # Allow any token that looks reasonable (GitHub may change formats)
        if not re.match(r'^[a-zA-Z0-9_-]+$', token):
            raise ValidationError("GitHub token contains invalid characters")
    
    return token


def validate_repository_name(repo_name: str) -> str:
    """
    Validate GitHub repository name format (owner/repo).
    
    Args:
        repo_name: Repository name in format "owner/repo"
        
    Returns:
        The validated repository name
        
    Raises:
        ValidationError: If repository name format is invalid
    """
    if not repo_name:
        raise ValidationError("Repository name cannot be empty")
    
    if '/' not in repo_name:
        raise ValidationError("Repository name must be in format 'owner/repo'")
    
    parts = repo_name.split('/')
    if len(parts) != 2:
        raise ValidationError("Repository name must be in format 'owner/repo'")
    
    owner, repo = parts
    
    # Validate owner name
    if not owner or not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$', owner):
        raise ValidationError(f"Invalid owner name: {owner}")
    
    # Validate repository name
    if not repo or not re.match(r'^[a-zA-Z0-9._-]+$', repo):
        raise ValidationError(f"Invalid repository name: {repo}")
    
    return repo_name


def validate_topic_name(topic: str) -> str:
    """
    Validate GitHub topic name.
    
    Args:
        topic: Topic name to validate
        
    Returns:
        The validated topic name
        
    Raises:
        ValidationError: If topic name is invalid
    """
    if not topic:
        raise ValidationError("Topic name cannot be empty")
    
    # GitHub topics are lowercase, alphanumeric, and can contain hyphens
    if not re.match(r'^[a-z0-9-]+$', topic.lower()):
        raise ValidationError(f"Invalid topic name: {topic}. Topics must be lowercase alphanumeric with hyphens")
    
    if len(topic) > 50:
        raise ValidationError(f"Topic name too long: {topic}. Maximum 50 characters")
    
    return topic.lower()


def validate_limit(limit: int, min_val: int = 1, max_val: int = 1000) -> int:
    """
    Validate limit parameter.
    
    Args:
        limit: Limit value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        The validated limit
        
    Raises:
        ValidationError: If limit is out of range
    """
    if not isinstance(limit, int):
        raise ValidationError("Limit must be an integer")
    
    if limit < min_val:
        raise ValidationError(f"Limit must be at least {min_val}")
    
    if limit > max_val:
        raise ValidationError(f"Limit cannot exceed {max_val}")
    
    return limit


def validate_mongodb_uri(uri: str) -> str:
    """
    Validate MongoDB connection URI.
    
    Args:
        uri: MongoDB URI to validate
        
    Returns:
        The validated URI
        
    Raises:
        ValidationError: If URI format is invalid
    """
    if not uri:
        raise ValidationError("MongoDB URI cannot be empty")
    
    try:
        parsed = urlparse(uri)
        if parsed.scheme not in ['mongodb', 'mongodb+srv']:
            raise ValidationError("MongoDB URI must start with 'mongodb://' or 'mongodb+srv://'")
    except Exception as e:
        raise ValidationError(f"Invalid MongoDB URI format: {e}")
    
    return uri


def validate_language(language: str) -> str:
    """
    Validate programming language name.
    
    Args:
        language: Programming language name
        
    Returns:
        The validated language name
        
    Raises:
        ValidationError: If language name is invalid
    """
    if not language:
        raise ValidationError("Language name cannot be empty")
    
    # Allow common programming language names
    if not re.match(r'^[a-zA-Z0-9+#.-]+$', language):
        raise ValidationError(f"Invalid language name: {language}")
    
    return language


def validate_topics_list(topics: List[str]) -> List[str]:
    """
    Validate a list of topic names.
    
    Args:
        topics: List of topic names to validate
        
    Returns:
        List of validated topic names
        
    Raises:
        ValidationError: If any topic name is invalid
    """
    if not topics:
        raise ValidationError("Topics list cannot be empty")
    
    validated_topics = []
    for topic in topics:
        validated_topics.append(validate_topic_name(topic))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_topics = []
    for topic in validated_topics:
        if topic not in seen:
            seen.add(topic)
            unique_topics.append(topic)
    
    return unique_topics


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters.
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Sanitized filename
    """
    if not filename:
        return "unnamed"
    
    # Remove invalid characters for filenames
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(' .')
    
    # Ensure it's not empty after sanitization
    if not sanitized:
        return "unnamed"
    
    return sanitized
