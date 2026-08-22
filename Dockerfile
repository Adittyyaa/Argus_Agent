FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create audit database directory
RUN mkdir -p /app/data

# Expose ports
EXPOSE 8000 8001 8002 8003 8501

# Default command (can be overridden in docker-compose)
CMD ["python", "coordinator/main.py"]