#!/bin/bash

# Stop MongoDB Docker containers
# This script stops the MongoDB container while preserving data

set -e

echo "🛑 Stopping MongoDB containers..."

cd docker

# Try Docker Compose V2 first, fallback to V1
if docker compose version > /dev/null 2>&1; then
    docker compose down
elif command -v docker-compose > /dev/null 2>&1; then
    docker-compose down
else
    echo "❌ Docker Compose not found."
    exit 1
fi

echo "✅ MongoDB containers stopped successfully!"
echo "💾 Data is preserved in Docker volumes"
echo ""
echo "🔄 To restart: ./scripts/start-db.sh"
echo "🗑️  To remove all data: docker compose down -v (or docker-compose down -v)"
