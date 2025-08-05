#!/bin/bash

# GitHub Contributors Analyzer - Setup Script
# This script sets up the development environment

set -e

echo "🚀 Setting up GitHub Contributors Analyzer..."

# Check if Python 3.8+ is available
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.8+ is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Copy environment file
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your GitHub token and other settings"
else
    echo "✅ .env file already exists"
fi

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo "🐳 Docker found. You can start MongoDB with: ./scripts/start-db.sh"
else
    echo "⚠️  Docker not found. Please install Docker to use the MongoDB setup"
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your GitHub token"
echo "2. Start MongoDB: ./scripts/start-db.sh"
echo "3. Run the analyzer: python -m src.github_analyzer.cli --help"
echo ""
