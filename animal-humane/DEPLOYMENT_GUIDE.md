# Deployment Guide: Robust Scheduling Solutions

This guide provides multiple options for running your Animal Humane scraper and diff analyzer without depending on your laptop being awake.

## Option 1: Docker Container (Recommended)

**Pros**: Easy to deploy anywhere, consistent environment, automatic restarts
**Best for**: Running on a home server, VPS, or cloud instance

### Setup:
```bash
cd animal-humane/deployment/docker
docker-compose up -d
```

This will:
- Start Elasticsearch in a container
- Start the scheduler in a container
- Automatically restart if containers crash
- Save logs and reports to local directories

### Management:
```bash
# View logs
docker-compose logs -f scheduler

# Stop services
docker-compose down

# Update and restart
docker-compose pull && docker-compose up -d
```

## Option 2: System Service (Linux/macOS)

**Pros**: Runs as system service, starts on boot, managed by OS
**Best for**: Dedicated server or always-on machine

### Setup:
1. **Edit the service file**:
   ```bash
   # Edit paths in the service file
   nano deployment/systemd/animal-humane-scheduler.service
   ```

2. **Install the service**:
   ```bash
   sudo cp deployment/systemd/animal-humane-scheduler.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable animal-humane-scheduler
   sudo systemctl start animal-humane-scheduler
   ```

3. **Check status**:
   ```bash
   sudo systemctl status animal-humane-scheduler
   sudo journalctl -u animal-humane-scheduler -f
   ```

## Option 3: Cloud Functions (Serverless)

**Pros**: No server maintenance, pay-per-use, highly reliable
**Best for**: Production deployment with minimal maintenance

### Google Cloud Setup:
```bash
# Deploy scraping function
gcloud functions deploy animal-humane-scraper \
  --runtime python39 \
  --trigger-http \
  --entry-point scrape_and_index \
  --source deployment/cloud/

# Deploy diff analysis function
gcloud functions deploy animal-humane-diff \
  --runtime python39 \
  --trigger-http \
  --entry-point run_diff_analysis \
  --source deployment/cloud/

# Schedule with Cloud Scheduler
gcloud scheduler jobs create http scrape-job \
  --schedule="0 8,12,16,20 * * *" \
  --uri="https://YOUR-REGION-YOUR-PROJECT.cloudfunctions.net/animal-humane-scraper"
```

## Option 4: Background Process (Simple)

**Pros**: Simple, no additional setup required
**Best for**: Testing or temporary solutions

### Setup:
```bash
# Run in background with nohup
nohup python scheduler/background_scheduler.py > scheduler.log 2>&1 &

# Or use screen/tmux
screen -S animal-humane
python scheduler/background_scheduler.py
# Ctrl+A, D to detach
```

## Diff Analysis Features

The new diff analyzer provides:

### Automatic Analysis:
- Compares most recent index with previous index
- Runs twice daily (9 AM and 9 PM)
- Identifies new, removed, and changed dogs

### Output Files:
- **JSON Report**: `diff_reports/diff_report_TIMESTAMP.json` - Complete data
- **Summary Report**: `diff_reports/diff_summary_TIMESTAMP.txt` - Human readable
- **CSV Report**: `diff_reports/changes_TIMESTAMP.csv` - Spreadsheet compatible

### Manual Analysis:
```bash
# Run diff analysis manually
python scheduler/diff_analyzer.py

# Analyze specific time period
python -c "
from scheduler.diff_analyzer import DiffAnalyzer
analyzer = DiffAnalyzer()
analyzer.analyze_differences()
"
```

## Configuration

### Environment Variables:
```bash
# Elasticsearch connection
export ELASTICSEARCH_HOST=http://localhost:9200

# Scraping configuration
export SHELTER_URL=https://animalhumanenm.org/adopt/adoptable-dogs/

# Output directories
export DIFF_REPORTS_DIR=./diff_reports
export LOG_DIR=./logs
```

### Schedule Customization:
Edit `scheduler/background_scheduler.py` to modify:
- Scraping frequency (currently 4 times daily)
- Diff analysis frequency (currently twice daily)
- Health check frequency (currently hourly)

## Monitoring and Alerts

### Log Files:
- `scheduler.log` - Main scheduler log
- `diff_reports/` - Analysis reports
- Docker logs via `docker-compose logs`

### Health Checks:
The scheduler includes automatic health checks that:
- Verify Elasticsearch connectivity
- Log status every hour
- Can be extended to send alerts

### Adding Email Alerts:
```python
# Add to scheduler/background_scheduler.py
import smtplib
from email.mime.text import MIMEText

def send_alert(subject, message):
    # Configure your email settings
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    email = "your-email@gmail.com"
    password = "your-app-password"
    
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = email
    msg['To'] = email
    
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(email, password)
        server.send_message(msg)
```

## Troubleshooting

### Common Issues:

1. **Elasticsearch Connection Failed**:
   - Check if Elasticsearch is running
   - Verify host/port configuration
   - Check firewall settings

2. **Scraping Errors**:
   - Website might be down
   - HTML structure changed
   - Network connectivity issues

3. **Permission Errors**:
   - Check file/directory permissions
   - Ensure user has write access to log/report directories

### Debug Mode:
```bash
# Run with debug logging
PYTHONPATH=/path/to/animal-humane python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from scheduler.background_scheduler import AnimalHumaneScheduler
scheduler = AnimalHumaneScheduler()
scheduler.scrape_and_index()
"
```

## Recommended Setup

For most users, I recommend **Option 1 (Docker)** because:
- ✅ Easy to set up and manage
- ✅ Consistent environment
- ✅ Automatic restarts
- ✅ Easy to move between machines
- ✅ Includes Elasticsearch
- ✅ Persistent data storage

Simply run:
```bash
cd animal-humane/deployment/docker
docker-compose up -d
```

And your scraper will run reliably without depending on your laptop!