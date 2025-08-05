"""
Custom exceptions for GitHub Contributors Analyzer.
"""


class GitHubAnalyzerError(Exception):
    """Base exception for GitHub Contributors Analyzer."""
    pass


class ConfigurationError(GitHubAnalyzerError):
    """Raised when there's a configuration issue."""
    pass


class GitHubAPIError(GitHubAnalyzerError):
    """Raised when GitHub API returns an error."""
    
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class RateLimitExceededError(GitHubAPIError):
    """Raised when GitHub API rate limit is exceeded."""
    
    def __init__(self, reset_time: int = None):
        super().__init__("GitHub API rate limit exceeded")
        self.reset_time = reset_time


class DatabaseError(GitHubAnalyzerError):
    """Raised when there's a database operation error."""
    pass


class AuthenticationError(GitHubAnalyzerError):
    """Raised when GitHub authentication fails."""
    pass


class ValidationError(GitHubAnalyzerError):
    """Raised when input validation fails."""
    pass
