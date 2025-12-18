#!/bin/bash
# Stop all Animal Humane containers and restart them

echo "Stopping all containers..."
docker-compose down

echo "Rebuilding and starting all containers..."
docker-compose up --build -d

echo "Checking container status..."
docker-compose ps

echo "All containers have been restarted."
