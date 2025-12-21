# Dockerfile for running the scheduler in a container
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including Chromium for Selenium
RUN apt-get update && apt-get install -y \
    curl \
    tzdata \
    supervisor \
    wget \
    gnupg \
    ca-certificates \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set timezone to Mountain Time
ENV TZ=America/Denver
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make start.sh executable
RUN chmod +x start.sh

# Set environment variables
ENV PYTHONPATH=/app
ENV ELASTICSEARCH_HOST=http://elasticsearch:9200

# Run the API
CMD ["./start.sh"]