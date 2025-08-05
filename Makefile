# GitHub Contributors Analyzer - Development Makefile

.PHONY: help install test lint format clean setup start-db stop-db

help: ## Show this help message
	@echo "GitHub Contributors Analyzer - Development Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

setup: ## Run the setup script
	./scripts/setup.sh

test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ --cov=src --cov-report=html --cov-report=term

lint: ## Run linting
	flake8 src/ tests/

format: ## Format code
	black src/ tests/

type-check: ## Run type checking
	mypy src/

check-all: lint type-check test ## Run all checks

start-db: ## Start MongoDB with Docker
	./scripts/start-db.sh

stop-db: ## Stop MongoDB
	./scripts/stop-db.sh

clean: ## Clean up generated files
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

analyze-topics: ## Example: Analyze Python repositories
	python -m src.github_analyzer.cli analyze-topics python --limit 10 --save

trending: ## Example: Get trending Python repositories
	python -m src.github_analyzer.cli trending --language python --limit 10

stats: ## Show database statistics
	python -m src.github_analyzer.cli stats
