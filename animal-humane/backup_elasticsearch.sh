#!/bin/bash
# Backup Elasticsearch data from Docker

echo "💾 Backing up Elasticsearch Data"
echo "================================"

BACKUP_DIR="./elasticsearch_backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📁 Creating backup in: $BACKUP_DIR"

# Method 1: Export indices as JSON
echo "📤 Exporting indices..."
docker exec animal-humane-elasticsearch curl -X GET "localhost:9200/_cat/indices?v" > "$BACKUP_DIR/indices_list.txt"

# Export each animal-humane index
docker exec animal-humane-elasticsearch curl -X GET "localhost:9200/animal-humane-*/_search?size=10000" > "$BACKUP_DIR/all_data.json"

# Method 2: Create Elasticsearch snapshot (more reliable)
echo "📸 Creating Elasticsearch snapshot..."
docker exec animal-humane-elasticsearch curl -X PUT "localhost:9200/_snapshot/backup_repo" -H 'Content-Type: application/json' -d'
{
  "type": "fs",
  "settings": {
    "location": "/usr/share/elasticsearch/backups"
  }
}'

docker exec animal-humane-elasticsearch curl -X PUT "localhost:9200/_snapshot/backup_repo/backup_$(date +%Y%m%d_%H%M%S)" -H 'Content-Type: application/json' -d'
{
  "indices": "animal-humane-*",
  "ignore_unavailable": true,
  "include_global_state": false
}'

echo "✅ Backup completed in: $BACKUP_DIR"
echo ""
echo "📋 Backup contains:"
echo "   - indices_list.txt: List of all indices"
echo "   - all_data.json: Complete data export"
echo "   - Elasticsearch snapshot in container"