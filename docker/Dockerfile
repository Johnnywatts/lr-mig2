FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs && \
    chmod 777 /app/logs

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Explicitly install PyYAML (even if in requirements.txt, for certainty)
RUN pip install pyyaml>=6.0

# Copy application code
COPY src/ ./src/
COPY sql/ ./sql/

# Set environment variables
ENV PYTHONPATH=/app
ENV RUNNING_IN_DOCKER=true

# Command to run the application
CMD ["python", "-m", "src"] 