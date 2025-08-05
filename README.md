# GitHub Contributors Analyzer 2.0

A modern, comprehensive tool for analyzing GitHub repositories and their top contributors using GitHub's GraphQL API and MongoDB for data storage.

## ✨ Features

- 🚀 **Modern Architecture**: Built with Python 3.12+, async/await, and modern dependencies
- 🔍 **GitHub GraphQL API**: Uses GitHub's powerful GraphQL API instead of web scraping
- 📊 **Rich CLI Interface**: Beautiful command-line interface with progress bars and tables
- 🐳 **Docker Support**: Easy MongoDB setup with Docker Compose
- 💾 **Persistent Storage**: MongoDB with proper indexing and data persistence
- 🔒 **Secure Configuration**: Environment-based configuration with validation
- 📈 **Rate Limiting**: Intelligent rate limiting to respect GitHub API limits
- 🎯 **Topic-Based Analysis**: Analyze repositories by topics/tags
- 👥 **Contributor Insights**: Detailed contributor analysis and statistics

## 🚀 Quick Start

### Prerequisites

- Python 3.8+ (Python 3.12+ recommended)
- Docker and Docker Compose (for MongoDB)
- GitHub Personal Access Token

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/gajeshbhat/GH-Contributors-Analyzer.git
   cd GH-Contributors-Analyzer
   ```

2. **Run the setup script**:
   ```bash
   ./scripts/setup.sh
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env file with your GitHub token and other settings
   ```

4. **Start MongoDB**:
   ```bash
   ./scripts/start-db.sh
   ```

5. **Activate virtual environment**:
   ```bash
   source venv/bin/activate
   ```

### Usage

#### Analyze repositories by topics
```bash
python -m src.github_analyzer.cli analyze-topics python machine-learning --limit 50 --contributors 25 --save
```

#### List repositories from database
```bash
python -m src.github_analyzer.cli list-repositories --topic python --limit 20
```

#### Show contributors for a specific repository
```bash
python -m src.github_analyzer.cli contributors microsoft/vscode --limit 20
```

#### View database statistics
```bash
python -m src.github_analyzer.cli stats
```

#### Get trending repositories
```bash
python -m src.github_analyzer.cli trending --language python --limit 20 --save
```

#### Clear all database data
```bash
python -m src.github_analyzer.cli clear-data --confirm
```

## 📋 Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `analyze-topics` | Analyze repositories and contributors for given topics | `analyze-topics python rust --save` |
| `list-repositories` | List repositories from database | `list-repositories --topic python` |
| `contributors` | Show contributors for a repository | `contributors microsoft/vscode` |
| `stats` | Show database statistics | `stats` |
| `trending` | Fetch trending repositories | `trending --language python --save` |
| `clear-data` | Clear all database data | `clear-data --confirm` |

## ⚙️ Configuration

The application uses environment variables for configuration. Copy `.env.example` to `.env` and configure:

```env
# GitHub API Configuration
GITHUB_TOKEN=your_github_personal_access_token_here
GITHUB_API_URL=https://api.github.com/graphql

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=github_contributors
MONGODB_COLLECTION=repositories

# Application Configuration
LOG_LEVEL=INFO
MAX_REPOSITORIES_PER_TOPIC=100
MAX_CONTRIBUTORS_PER_REPO=100
RATE_LIMIT_REQUESTS_PER_HOUR=5000
```

## 🐳 Docker Setup

The project includes a complete Docker setup for MongoDB:

```bash
# Start MongoDB and Mongo Express
./scripts/start-db.sh

# Stop MongoDB
./scripts/stop-db.sh

# Access Mongo Express (Web UI)
# http://localhost:8081
```

## 🏗️ Architecture

```
├── src/github_analyzer/     # Main application package
│   ├── __init__.py          # Package initialization
│   ├── __main__.py          # Main entry point
│   ├── cli.py              # Command-line interface with Rich UI
│   ├── config.py           # Configuration management with Pydantic
│   ├── github_client.py    # GitHub GraphQL API client with rate limiting
│   ├── database.py         # MongoDB handler with async operations
│   ├── exceptions.py       # Custom exceptions
│   ├── logging_config.py   # Structured logging configuration
│   └── validators.py       # Input validation utilities
├── tests/                   # Test suite
│   ├── conftest.py         # Pytest fixtures and configuration
│   ├── test_cli.py         # CLI command tests
│   ├── test_config.py      # Configuration tests
│   └── test_github_client.py # GitHub client tests
├── docker/                  # Docker configuration
│   ├── docker-compose.yml  # MongoDB and Mongo Express setup
│   └── init-mongo.js       # MongoDB initialization script
├── scripts/                 # Utility scripts
│   ├── setup.sh            # Development environment setup
│   ├── start-db.sh         # Start MongoDB containers
│   └── stop-db.sh          # Stop MongoDB containers
├── .env.example            # Environment variables template
├── Makefile               # Development task automation
├── pytest.ini            # Pytest configuration
└── requirements.txt       # Python dependencies
```

## 🔧 Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -r requirements.txt

# Or use the Makefile for common tasks
make help          # Show all available commands
make install       # Install dependencies
make test          # Run tests
make test-cov      # Run tests with coverage
make format        # Format code
make lint          # Run linting
make type-check    # Run type checking
make check-all     # Run all checks
make clean         # Clean up generated files
```

#### Manual Commands

```bash
# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=src --cov-report=html

# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

### Testing

The project includes comprehensive tests for all major components:

- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test component interactions and CLI commands
- **Async Tests**: Proper testing of async/await functionality
- **Mock Tests**: Use mocks to test external API interactions without making real requests

```bash
# Run all tests
make test

# Run tests with coverage report
make test-cov

# Run specific test file
pytest tests/test_cli.py -v

# Run tests matching a pattern
pytest tests/ -k "test_github_client" -v
```

### Database Schema

#### Repositories Collection
```json
{
  "id": "repository_id",
  "name": "repository_name",
  "owner": "owner_name",
  "description": "Repository description",
  "url": "https://github.com/owner/repo",
  "stargazers_count": 1000,
  "forks_count": 100,
  "watchers_count": 50,
  "language": "Python",
  "topics": ["python", "machine-learning"],
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-12-01T00:00:00Z",
  "is_fork": false,
  "is_archived": false,
  "last_analyzed": "2024-01-01T00:00:00Z"
}
```

#### Contributors Collection
```json
{
  "repository_id": "repository_id",
  "repository_owner": "owner_name",
  "repository_name": "repository_name",
  "login": "contributor_username",
  "id": "contributor_id",
  "avatar_url": "https://avatars.githubusercontent.com/...",
  "html_url": "https://github.com/contributor",
  "contributions": 150,
  "type": "User",
  "last_updated": "2024-01-01T00:00:00Z"
}
```

## 🔧 Troubleshooting

### Common Issues

#### GitHub Token Issues
```bash
# Error: GitHub token not found
# Solution: Set your GitHub token in .env file
echo "GITHUB_TOKEN=your_token_here" >> .env
```

#### MongoDB Connection Issues
```bash
# Error: Database connection failed
# Solution: Start MongoDB using Docker
make start-db

# Or manually:
./scripts/start-db.sh
```

#### Rate Limiting
```bash
# Error: API rate limit exceeded
# Solution: The client automatically handles rate limiting, but you can:
# 1. Use a GitHub token with higher limits
# 2. Reduce the number of requests per hour in .env
# 3. Wait for the rate limit to reset
```

#### Import Errors
```bash
# Error: ModuleNotFoundError
# Solution: Make sure you're in the project root and using the correct Python path
python -m src.github_analyzer.cli --help

# Or activate your virtual environment
source venv/bin/activate
```

### Getting Help

- Check the logs in the application output for detailed error messages
- Use the `--log-level DEBUG` flag for more verbose logging
- Ensure all dependencies are installed: `make install`
- Verify your `.env` file is properly configured
- Check that MongoDB is running: `docker ps`

## 📝 Changelog

### Version 2.0 (Current)
- **Complete rewrite** with modern Python architecture
- **GraphQL API**: Migrated from web scraping to GitHub's official GraphQL API
- **Async/Await**: Full async support for better performance
- **Rich CLI**: Beautiful command-line interface with progress bars and tables
- **Docker Support**: Easy MongoDB setup with Docker Compose
- **Comprehensive Testing**: Unit tests, integration tests, and mocking
- **Modern Dependencies**: Updated to latest versions of all libraries
- **Type Safety**: Added type hints and validation with Pydantic
- **Structured Logging**: Better logging with structured output
- **Rate Limiting**: Intelligent rate limiting to respect GitHub API limits

### Legacy Version (Pre-2.0)
- Basic web scraping functionality
- Simple MongoDB integration
- Command-line interface
- Topic and contributor analysis

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `make test`
5. Format your code: `make format`
6. Run linting: `make lint`
7. Commit your changes: `git commit -am 'Add feature'`
8. Push to the branch: `git push origin feature-name`
9. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- GitHub for providing the excellent GraphQL API
- The Python community for the amazing libraries used in this project
- Contributors who helped improve this tool
