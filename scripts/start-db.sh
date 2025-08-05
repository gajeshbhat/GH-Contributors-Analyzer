#!/bin/bash

# Start MongoDB using Docker Compose
# This script starts the MongoDB container with persistent storage

set -e

echo "🐳 Starting MongoDB with Docker Compose..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your MongoDB credentials"
fi

# Start the services
cd docker

# Try Docker Compose V2 first, fallback to V1
if docker compose version > /dev/null 2>&1; then
    echo "Using Docker Compose V2..."
    docker compose up -d
elif command -v docker-compose > /dev/null 2>&1; then
    echo "Using Docker Compose V1..."
    docker-compose up -d
else
    echo "❌ Docker Compose not found. Please install Docker Compose."
    exit 1
fi

echo "✅ MongoDB started successfully!"
echo ""
echo "📊 Services:"
echo "  - MongoDB: http://localhost:27017"
echo "  - Mongo Express (Web UI): http://localhost:8081"
echo ""
echo "🔍 Check status: docker compose ps (or docker-compose ps)"
echo "📋 View logs: docker compose logs -f (or docker-compose logs -f)"
echo "🛑 Stop services: ./scripts/stop-db.sh"
