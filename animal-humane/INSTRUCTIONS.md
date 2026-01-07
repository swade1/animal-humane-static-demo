# Animal Humane Static Portfolio Demo - Complete Instructions

## Overview
This document provides comprehensive instructions for maintaining and updating the Animal Humane static portfolio demo. This system converts a live dashboard into a static version suitable for portfolio demonstration.

Vercel URL:         https://animal-humane-static-demo.vercel.app/
GitHub Workflows:   https://github.com/swade1/animal-humane-static-demo/actions
Vercel Dashboard:   https://vercel.com/susanwade09-6829s-projects
Vercel Deployments: https://vercel.com/susanwade09-6829s-projects/animal-humane-static-demo/deployments 

---

## 1. Technology Stack

### Core Technologies
- **React Frontend**: JavaScript web application built with React 18
- **Vercel**: Cloud platform for static site hosting and deployment
- **GitHub**: Version control and repository hosting with automated workflows
- **Elasticsearch**: Document database running on two instances (ports 9200 and 9201)
- **Python 3**: Backend scripts for data processing and updates
- **GitHub Actions**: Automated CI/CD workflows for continuous updates

### Key Files and Components
- **React App**: `react-app/` - The frontend application
- **Static API**: `react-app/public/api/` - JSON files that simulate API responses
- **Location Data**: `location_info.jsonl` - Master file containing dog location/origin data
- **Update Scripts**: `update_static_data.py` - Comprehensive data update automation
  - Updates these 2 things:
    1. last-updated.json - Updates timestamp based on latest Elasticsearch index
    2. location_info.jsonl - Copies from root directory to public directory
- **GitHub Workflows**: `.github/workflows/` - Automated deployment and update processes

### Deployment Architecture
```
Local Development → GitHub Repository → GitHub Actions → Vercel Deployment
      ↓                    ↓                 ↓              ↓
Elasticsearch(9200)   Version Control   Auto Updates   Live Demo Site
      ↑
Elasticsearch(9201) 
  (Backup)
```

---

## 2. System Workflow and Component Interactions

### Data Flow Process

1. **Data Source**: Elasticsearch indices contain live animal data
   - Primary instance: `localhost:9200` (Docker)
   - Backup instance: `localhost:9201` (Secondary)

2. **Data Processing**: Python scripts query Elasticsearch and generate static files
   - Queries latest animal-humane index for timestamp information
   - Processes location_info.jsonl for "Available Soon" dogs
   - Generates JSON files for React app consumption

3. **Static Generation**: React app reads static JSON files instead of live API
   - `last-updated.json`: Contains timestamp from latest ES index
   - `recent-pupdates.json`: Dog status and change information
   - `location_info.jsonl`: Geographic and origin data for dogs

4. **Deployment Pipeline**: 
   - Local changes → Git commit → GitHub repository
   - GitHub Actions automatically run update scripts every 2 hours
   - Vercel deploys updated static files to live demo site

### Component Interactions

**Elasticsearch ↔ Python Scripts**
- Scripts query ES indices using REST API on port 9200
- Extract timestamps from index names (format: animal-humane-YYYYMMDD-HHMM)
- Generate accurate "last updated" information for portfolio demo

**Python Scripts ↔ React App**
- Scripts generate JSON files in `react-app/public/api/`
- React components consume these static files as if they were live API responses
- Demo banner shows data freshness based on ES index timestamps

**GitHub ↔ Vercel**
- Git pushes trigger Vercel deployments automatically
- GitHub Actions run scheduled updates to keep demo current
- Vercel serves the static React build with updated data files

---

## 3. Detailed Update Instructions

### A. Updating the code: Example - Removing Blue Banner
1. **Edit the App.js file** - remove the import for the DemoBanner component and the <DemoBanner/> element
2. **Commit and push the changes**
   ```
   git add react-app/src/App.js
   git commit -m "Remove blue demo banner from portfolio site"
   git push origin main
   # after getting a reject message because the remote contains work I don't have locally.
   git pull origin main --rebase && git push origin main
   ```
   What happens next: 
   GitHub Side  
   1. Git push completes. The changes are in the GitHub repo
   2. GitHub actions may trigger - since you pushed to the main branch, it could trigger the workflow
   3. Repo is updated. The main branch contains the App.js change without DemoBanner.
   Vercel Side  
   1. Webhook triggers - Vercel detects the new commit on the main branch 
   2. Build starts automatically 
      - Runs npm install to install dependencies
      - Runs npm run build to create production build
      - The build uses the updated App.js (without DemoBanner)
   3. Deployment - new version is deployed to the live URL
   4. Live site updates - within 1-2 minutes, https://animal-humane-static-demo.vercel.app will show the version without the blue banner. 

### A. Updating location_info.jsonl

The `location_info.jsonl` file contains critical data for identifying dogs in the "Available Soon" category. These are dogs that exist in your location database but haven't yet appeared in the main Elasticsearch indices.

#### Step-by-Step Process:

1. **Navigate to Project Directory**
   ```bash
   cd /Users/swade/KIRO-project/professional-portfolio/animal-humane
   ```

2. **Edit the Master Location File**
   ```bash
   # Open in your preferred editor (example with vim)
   vim location_info.jsonl
   
   # OR use VS Code
   code location_info.jsonl
   ```

3. **Update Dog Records**
   Each line should be a valid JSON object with this structure:
   ```json
   {"name":"DogName","id":123456789,"origin":"Shelter Name","returned":0,"bite_quarantine":0,"latitude":35.1234,"longitude":-106.5678}
   ```
   
   **Required Fields:**
   - `name`: Dog's name (string)
   - `id`: Unique shelter ID (integer)  
   - `origin`: Source shelter or "Owner Surrender"/"Stray" (string)
   - `returned`: 1 if previously returned, 0 if not (integer)
   - `bite_quarantine`: 1 if in quarantine, 0 if not (integer)
   
   **Optional Fields:**
   - `latitude`: GPS latitude (float)
   - `longitude`: GPS longitude (float)

4. **Run the Update Script**
   ```bash
   # Activate Python environment
   source .venv/bin/activate
   
   # Run comprehensive update script
   python update_static_data.py
   ```
   
   **Expected Output:**
   ```
   🔄 Updating static data for portfolio demo...
   📊 Latest index: animal-humane-20260101-1951
   ✅ Updated timestamp file:
      📅 Date: January 01, 2026 at 07:51 PM UTC
      🔍 Source: animal-humane-20260101-1951
   ✅ Synced location_info.jsonl to React public directory
      📊 634 dog records synchronized
   🎉 Static data update complete!
   ```

5. **Commit and Deploy Changes**
   ```bash
   # Add all changes to git
   git add location_info.jsonl react-app/public/location_info.jsonl react-app/public/api/last-updated.json
   
   # Commit with descriptive message
   git commit -m "Update location info with new dog data - $(date +%Y-%m-%d)"
   
   # Push to trigger deployment
   git push origin main
   ```

6. **Verify Deployment**
   - Check the live site: https://animal-humane-static-demo.vercel.app
   - Look for updated timestamp in the demo banner
   - Verify "Available Soon" section shows correct dogs

### B. Migrating Elasticsearch Indices from Backup (9201) to Primary (9200)

When you need to move data from your backup Elasticsearch instance (port 9201) to your primary instance (port 9200):

#### Prerequisites Check:
```bash
# Verify both Elasticsearch instances are running
curl -X GET "localhost:9200/_cluster/health?pretty"
curl -X GET "localhost:9201/_cluster/health?pretty"

# Both should return status "green" or "yellow"
```

#### Step 1: List Available Indices

**Check what's available on backup (9201):**
```bash
curl -X GET "localhost:9201/_cat/indices/animal-humane-*?v"
```

**Check what exists on primary (9200):**
```bash
curl -X GET "localhost:9200/_cat/indices/animal-humane-*?v"
```

#### Step 2: Choose Migration Method

**Option A: Manual Index Copy (Recommended for single indices)**

1. **Create snapshot repository on source (9201):**
   ```bash
   curl -X PUT "localhost:9201/_snapshot/migrate_repo" -H 'Content-Type: application/json' -d'
   {
     "type": "fs",
     "settings": {
       "location": "/tmp/elasticsearch-snapshots"
     }
   }'
   ```

2. **Create matching repository on destination (9200):**
   ```bash
   curl -X PUT "localhost:9200/_snapshot/migrate_repo" -H 'Content-Type: application/json' -d'
   {
     "type": "fs",
     "settings": {
       "location": "/tmp/elasticsearch-snapshots"
     }
   }'
   ```

3. **Create snapshot of specific index on source:**
   ```bash
   # Replace YYYYMMDD-HHMM with actual index date/time
   curl -X PUT "localhost:9201/_snapshot/migrate_repo/migration_$(date +%Y%m%d_%H%M%S)" -H 'Content-Type: application/json' -d'
   {
     "indices": "animal-humane-YYYYMMDD-HHMM",
     "ignore_unavailable": true,
     "include_global_state": false
   }'
   ```

4. **Restore snapshot to destination:**
   ```bash
   curl -X POST "localhost:9200/_snapshot/migrate_repo/migration_$(date +%Y%m%d_%H%M%S)/_restore" -H 'Content-Type: application/json' -d'
   {
     "ignore_unavailable": true,
     "include_global_state": false
   }'
   ```

**Option B: Using Existing Migration Scripts**

1. **Run the migration script:**
   ```bash
   # Activate Python environment
   source .venv/bin/activate
   
   # Run migration (check available scripts)
   python migrate_specific_indices.py
 
   # If docker container for Elasticsearch isn't running, start it with: 
   cd deployment/docker && docker-compose up -d elasticsearch

   # Verify it's running
   curl http://localhost:9200/_cluster/health

   
   # OR for all data
   python migrate_data_to_docker.py
   ```

2. **Follow script prompts** to select which indices to migrate

#### Step 3: Verify Migration Success

1. **Check index was copied:**
   ```bash
   curl -X GET "localhost:9200/_cat/indices/animal-humane-*?v"
   ```

2. **Compare document counts:**
   ```bash
   # Count documents in source
   curl -X GET "localhost:9201/animal-humane-YYYYMMDD-HHMM/_count"
   
   # Count documents in destination  
   curl -X GET "localhost:9200/animal-humane-YYYYMMDD-HHMM/_count"
   
   # Numbers should match
   ```

3. **Test data integrity:**
   ```bash
   # Sample a few documents from both indices
   curl -X GET "localhost:9201/animal-humane-YYYYMMDD-HHMM/_search?size=5&pretty"
   curl -X GET "localhost:9200/animal-humane-YYYYMMDD-HHMM/_search?size=5&pretty"
   ```

#### Step 4: Update Static Demo Data

After successful migration, update your demo with the new data:

```bash
# Run comprehensive update to capture new timestamp
python update_static_data.py

# Commit changes
git add react-app/public/api/last-updated.json
git commit -m "Update demo timestamp after ES migration"
git push origin main
```

---

## 4. Troubleshooting Common Issues

### GitHub Actions Overwriting Timestamps
**Problem**: GitHub Actions runs every 2 hours and may overwrite your timestamp with fallback data.

**Solution**: 
```bash
git add .
git commit -m "Your message"
git pull origin main --rebase
git push origin main
```

### Elasticsearch Connection Refused
**Problem**: Scripts can't connect to Elasticsearch.

**Diagnosis**:
```bash
# Check if ES is running
curl -XGET "localhost:9200/"

# Check Docker containers
docker ps | grep elasticsearch
```

**Solution**:
```bash
# Start Docker Elasticsearch if needed
docker-compose up -d elasticsearch
```

### Vercel Not Deploying Changes
**Problem**: Changes aren't appearing on live site.

**Solution**:
```bash
# Force deployment with dummy change
echo "# Deploy trigger $(date)" > react-app/public/deploy.txt
git add react-app/public/deploy.txt
git commit -m "Force Vercel deployment"
git push origin main
```

### Location Data Not Loading
**Problem**: "Available Soon" section shows no dogs despite location_info.jsonl having data.

**Check**:
```bash
# Verify file was copied to React public directory
ls -la react-app/public/location_info.jsonl

# Check file format
head -5 react-app/public/location_info.jsonl
```

---

## 5. Maintenance Schedule

### Daily (Automatic)
- GitHub Actions runs every 2 hours to update timestamps
- Vercel automatically deploys any changes

### Weekly (Manual)
- Review error logs in GitHub Actions
- Check demo site functionality
- Update location_info.jsonl if new dogs arrive

### Monthly (Manual)
- Clean up old Elasticsearch snapshots
- Review and update documentation
- Test backup Elasticsearch instance

---

## 6. Important File Locations

### Configuration Files
- `react-app/package.json` - React app dependencies
- `.github/workflows/update-data.yml` - Automated update workflow
- `docker-compose.yml` - Elasticsearch container configuration

### Data Files
- `location_info.jsonl` - Master location database
- `react-app/public/location_info.jsonl` - Copy for React app
- `react-app/public/api/*.json` - Static API response files

### Scripts
- `update_static_data.py` - Main data update script
- `update_timestamp.py` - Legacy timestamp-only script
- `migrate_*.py` - Various Elasticsearch migration utilities

### Deployment
- `react-app/build/` - Production React build (auto-generated)
- Live site: https://animal-humane-static-demo.vercel.app

### Cron Schedule
- .github/workflows/update-data.yml 
---

## 7. Migrating Indices from 9201 to 9200 after migrate_specific_indices.py stopped working
0. Make sure index is updated before you start this process (all adoptions/location changes, etc.)
1. curl search for all docs in the index and output to index-name.json. 
   ```
   curl -XGET 'localhost:9201/index-name/_search?pretty&size=100' > index-name.json`
   ```
2. Run bulk_conversion.py 
   ```
    python bulk_conversion.py [raw output file] [bulk formatted output] [index name for {"index":{"_index":...}}]
    python bulk_conversion.py index-name.json index-name.jsonl index-name
   ```
3. Save output (index-name.jsonl) file to ~/Scripts/professional-portfolio/animal-humane/backups
4. Delete index_name.json 
5. To re-ingest into 9200, `curl -XPOST 'localhost:9200/_bulk?pretty' -H 'Content-Type:application/x-ndjson' --data-binary "@index-name.jsonl"`


## 8. Docker Operations 
1. List all files in the container matching the id given: docker exec -it 584ff75a3171 ls /app  
2. Find matching file names: docker exec -it <container_name_or_id> find /app -name "*.py"
3. Search for references to recent-pupdates.json in the /app directory. docker exec -it 584ff75a3171 grep -i "recent-pupdates.json" -r /app


## 9. Running manually
1. From the animal-humane directory in the virtual environment (source .venv/bin/activate) run 'python scheduler/background_scheduler.py'
    * Index created
    * animal-humane-latest alias created to point to this index
    * scraping and ingestion executes
2. Check scheduler.log in the animal-humane directory for any log such as:
    * "Starting diff analysis"
    * "Diff analysis completed. Found X changes"
    * Any errors or warnings related to diff analysis
3. If the diff analysis didn't kick off 10 minutes after index creation/scraping/ingest, try this:
   This is the way to run just diff-analysis on existing indices instead of creating a new index 
   at the same time.
   ```
   # In a Python shell, from the project root and inside the virtual environment:
   from scheduler.background_scheduler import AnimalHumaneScheduler
   scheduler = AnimalHumaneScheduler()
   scheduler.run_diff_analysis()
   ```
4. Push updates to the repo
   ```
   git add react-app/public/api/* react-app/public/missing_dogs.txt
   git commit -m "Update frontend data files with latest adoption/status changes"
   git push origin main
   ```



## 9. Contact Information

For technical issues or questions about this system:
- GitHub Repository: https://github.com/swade1/animal-humane-static-demo
- Vercel Dashboard: https://vercel.com/dashboard
- Local development: `localhost:3000` (when running `npm start`)

---

*Last updated: January 1, 2026*
*System version: Static Portfolio Demo v1.0*



Command to make the alias animal-humane-latest is pointing to last index (most current)
```
curl -X POST "localhost:9200/_aliases" -H 'Content-Type: application/json' -d'
{
  "actions": [
    { "remove": { "index": "*", "alias": "animal-humane-latest" } },
    { "add":    { "index": "animal-humane-20260102-1900", "alias": "animal-humane-latest" } }
  ]
}'
```


Steps to convert older indices to _bulk compatible format 
1. Output index contents to file: `curl -XGET 'localhost:9201/animal-humane-2025MMDD-HHmm/_search?pretty'&size=100' > animal-humane-2025MMDD-HHmm.json
2. Use the bulk_conversion.py script to convert the .json file to a _bulk POST compatible .jsonl file
   `bulk_conversion.py animal-humane-2025MMDD-HHmm.json animal-humane-2025MMDD-HHmm.jsonl animal-humane-2025MMDD-HHmm
3. Verify you have all the docs by checking number of lines in the file and that they match the number of docs in the corresponding index on 9200
4. Copy the .jsonl file to ~/Scripts/professional-portfolio/animal-humane/backups
5. Delete the .json file 
4. Delete both indices in 9201 and 9200.


Clear the api container cache
curl -sS -X POST http://127.0.0.1:8000/api/cache/clear | jq '.'



All documents indexed successfully.
Refreshing Elasticsearch to ensure doc availability
Index refreshed successfully.
2026-01-03 11:30:07,273 - INFO - Pushed 69 dogs to Elasticsearch (Indes only shows 63)
2026-01-03 11:30:07,294 - INFO - POST http://localhost:9200/_aliases [status:200 duration:0.020s]
2026-01-03 11:30:07,294 - INFO - Updated alias to point to animal-humane-20260103-1128



Strategy
Write scripts that collect your latest data (e.g., from Elasticsearch or your backend API) and output it to JSON files (like overview.json) in your React app’s public/api directory.


Limit docker output 
docker ps --format "table {{.Names}}\t{{.Image}}"

Install vim-tiny in a container 
apt-get update && apt-get install -y vim-tiny


## Verification of Visualization Output
Query to verify weekly adoptions by age group
```
curl -X POST "http://localhost:9200/animal-humane-*/_search?pretty&_source=name,age_group" -H 'Content-Type: application/json' -d '{"size": 10000,"query": {"bool": {"must": [{ "term": { "status": "adopted" } },{ "range": { "timestamp": { "gt": "2025-12-29" } } }]}}}'
```

Query to verify shelter counts (available/adopted per shelter)
#Note: This query does not account for dogs that have been adopted and then returned like Littles. The output 
#will show 9 dogs in Tucumcari have been adopted (which is true) but one was returned so there are really 
#8 adopted and 1 available. The bar chart is picking up on this though and is correct. 
```
curl -XGET 'localhost:9200/animal-humane-*/_search?pretty&size=0' -H 'Content-Type:application/json' -d '{"query":{"match":{"origin.keyword":"City of Las Vegas Animal Care Center"}},"aggs":{"1":{"terms":{"field":"id","size":500},"aggs":{"2":{"terms":{"field":"status.keyword"}}}}}}' > LVACC_Count.json
```

To update available_soon section of Recent Pupdates tab:
Run find_missing_dogs.py
Copy missing_dogs.txt in animal-humane directory to react-app/public/missing_dogs.txt
run generate_recent_pupdates_json.py

Add, commit, and push to the repo.
