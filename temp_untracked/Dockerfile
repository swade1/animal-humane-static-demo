FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install supervisor
RUN pip install supervisor

# Copy supervisord configuration
COPY supervisord.conf /etc/supervisord.conf

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8000

# Set Python path to include the app root
ENV PYTHONPATH=/app

# Start supervisord
CMD ["/usr/local/bin/supervisord", "-c", "/etc/supervisord.conf"]