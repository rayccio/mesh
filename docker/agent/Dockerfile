FROM python:3.11-alpine

WORKDIR /app

# Copy requirements and install Python packages
COPY docker/agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent worker script
COPY docker/agent/agent_worker.py .

# Create data directory (will be mounted)
RUN mkdir /data

# No entrypoint – run worker directly
CMD ["python", "/app/agent_worker.py"]
