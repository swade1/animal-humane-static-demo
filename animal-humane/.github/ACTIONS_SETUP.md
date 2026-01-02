# GitHub Actions Configuration for Static Demo

This repository uses GitHub Actions to automatically update static demo data every 2 hours.

## Required Repository Secrets

To enable automated data updates, configure these secrets in your GitHub repository settings:

### Go to: Repository Settings → Secrets and variables → Actions → Repository secrets

1. **`API_BASE_URL`** (Required)
   - **Value**: `https://your-api-domain.com` or `http://your-server-ip:8000`
   - **Description**: Base URL of your live Animal Humane API server
   - **Security**: This should be your publicly accessible API endpoint

2. **`ELASTICSEARCH_HOST`** (Optional)
   - **Value**: `https://your-elasticsearch-domain.com:9200`
   - **Description**: Direct Elasticsearch host if API is not available
   - **Security**: Only if your Elasticsearch is publicly accessible with proper security

3. **`ELASTICSEARCH_USERNAME`** (Optional)
   - **Value**: Your Elasticsearch username
   - **Description**: Authentication for Elasticsearch (if required)
   - **Security**: Store securely, never expose in logs

4. **`ELASTICSEARCH_PASSWORD`** (Optional)
   - **Value**: Your Elasticsearch password
   - **Description**: Authentication for Elasticsearch (if required)
   - **Security**: Store securely, never expose in logs

## Workflow Features

### 🕐 Automatic Schedule
- Runs every 2 hours: `0 */2 * * *`
- Matches your current data scraping schedule
- Keeps demo data fresh without manual intervention

### 🛡️ Fallback Handling
- If data source is unavailable, keeps existing static files
- Updates timestamp to show when last update was attempted
- Graceful failure handling prevents broken deployments

### 🚀 Automatic Deployment
- Builds React app with updated data
- Deploys to GitHub Pages automatically
- Only rebuilds when data changes detected

### 🔒 Security Considerations

#### Minimal Permissions
```yaml
permissions:
  contents: write  # To commit updated data files
  pages: write     # To deploy to GitHub Pages
  id-token: write  # For GitHub Pages deployment
```

#### Network Security
- Workflow tests connectivity before attempting data export
- Handles network timeouts and connection failures
- Does not expose sensitive connection details in logs

#### IP Restrictions
If your Elasticsearch instance has IP restrictions:
- GitHub Actions runners use dynamic IPs
- Consider using a proxy or API gateway
- Alternative: Use webhook triggers instead of scheduled runs

## Testing the Workflow

### Manual Trigger
1. Go to: Repository → Actions → "Update Static Demo Data"
2. Click "Run workflow"
3. Monitor the execution in the Actions tab

### Monitor Automated Runs
- Check Actions tab for scheduled executions
- Review logs for any connection or data issues
- Verify updated timestamps in deployed demo

## Troubleshooting

### Common Issues

1. **"Cannot connect to data source"**
   - Expected behavior if API is not publicly accessible
   - Workflow will use fallback mode with cached data

2. **Build failures**
   - Check Node.js version compatibility
   - Verify package.json dependencies
   - Review React build logs

3. **Deployment issues**
   - Ensure GitHub Pages is enabled in repository settings
   - Check that `homepage` field in package.json matches repository

### Workflow Status
- ✅ Green: Data updated and deployed successfully
- 🟡 Yellow: Fallback mode (data source unavailable)
- ❌ Red: Build or deployment failure

## Development

### Local Testing
```bash
# Test the export script locally
python scripts/export_static_data.py

# Test React build with static mode
cd react-app
REACT_APP_STATIC_DEMO=true npm run build
```

### Modify Schedule
Edit `.github/workflows/update-data.yml`:
```yaml
schedule:
  - cron: '0 */4 * * *'  # Every 4 hours
  - cron: '0 9 * * *'    # Daily at 9 AM UTC
```

## Portfolio Demo Features

This automation enables:
- 🔄 **Fresh Data**: Demo always shows recent data
- 🤖 **Zero Maintenance**: Fully automated updates
- 💰 **Free Hosting**: Uses GitHub Pages (no server costs)
- 📱 **Always Available**: Static files never go down
- 🎯 **Portfolio Ready**: Professional automated demo

Perfect for showcasing your Animal Humane application to potential employers or clients!