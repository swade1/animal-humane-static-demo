#!/bin/bash
# Quick start script for Docker deployment

echo "🐳 Starting Animal Humane Docker Deployment"
echo "============================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is running"

# Navigate to docker directory
cd deployment/docker

# Create necessary directories for volume mounts
mkdir -p logs diff_reports

echo "📁 Created directories for logs and reports"

# Pull latest images and start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait a moment for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services are running!"
    echo ""
    echo "📊 Service Status:"
    docker-compose ps
    echo ""
    echo "📝 To view logs:"
    echo "   docker-compose logs -f scheduler"
    echo "   docker-compose logs -f elasticsearch"
    echo ""
    echo "📁 Reports will be saved to:"
    echo "   $(pwd)/diff_reports/"
    echo ""
    echo "🛑 To stop services:"
    echo "   docker-compose down"
    echo ""
    echo "🔄 To restart services:"
    echo "   docker-compose restart"
else
    echo "❌ Services failed to start. Check logs:"
    docker-compose logs
fi