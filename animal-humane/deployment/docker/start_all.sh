#!/bin/bash
# Start all Animal Humane containers

echo "Building and starting all containers..."
docker-compose up --build -d

echo "Checking container status..."
docker-compose ps

echo "All containers should now be running."
