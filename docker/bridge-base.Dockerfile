FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (if any, e.g., for cryptography)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bridge framework code
COPY backend/bridges /app/bridges
COPY backend/app/core /app/app/core

# Set Python path so bridges can import from app
ENV PYTHONPATH=/app

# The entrypoint will be overridden by channel-specific Dockerfiles
CMD ["python", "-m", "bridges.worker"]
