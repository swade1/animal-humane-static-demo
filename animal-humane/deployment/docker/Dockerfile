# Dockerfile for running the scheduler in a container
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Set timezone to Mountain Time
ENV TZ=America/Denver
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for logs and reports
RUN mkdir -p logs diff_reports

# Set environment variables
ENV PYTHONPATH=/app
ENV ELASTICSEARCH_HOST=http://elasticsearch:9200

# Run the scheduler
CMD ["python", "scheduler/background_scheduler.py"]