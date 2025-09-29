#!/bin/bash
# Script to migrate existing Elasticsearch data to Docker volume

echo "🔄 Migrating Elasticsearch Data to Docker"
echo "=========================================="

# Check if local Elasticsearch is running
if curl -s http://localhost:9200 > /dev/null; then
    echo "⚠️  Local Elasticsearch is running. Please stop it first:"
    echo "   brew services stop elasticsearch  # if using Homebrew"
    echo "   sudo systemctl stop elasticsearch  # if using systemd"
    exit 1
fi

# Start only Elasticsearch in Docker
echo "🚀 Starting Elasticsearch in Docker..."
cd deployment/docker
docker-compose up -d elasticsearch

# Wait for Elasticsearch to be ready
echo "⏳ Waiting for Elasticsearch to start..."
sleep 30

# Check if Elasticsearch is ready
until curl -s http://localhost:9200 > /dev/null; do
    echo "   Still waiting for Elasticsearch..."
    sleep 5
done

echo "✅ Elasticsearch is ready"

# If you have snapshots, you can restore them here
if [ -d "/path/to/your/elasticsearch/snapshots" ]; then
    echo "📁 Found existing snapshots. You can restore them manually:"
    echo "   1. Copy snapshots to Docker volume"
    echo "   2. Register snapshot repository"
    echo "   3. Restore snapshots"
    echo ""
    echo "   See: https://www.elastic.co/guide/en/elasticsearch/reference/current/snapshot-restore.html"
fi

echo "🎉 Migration setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Your Docker Elasticsearch is running on localhost:9200"
echo "   2. Start the scheduler: docker-compose up -d scheduler"
echo "   3. Your existing FastAPI/React apps will connect to Docker Elasticsearch"