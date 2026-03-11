FROM python:3.11-slim-bookworm AS builder

WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---------- Final stage ----------
FROM python:3.11-slim-bookworm

# Install only docker.io (no curl needed – healthcheck uses Python)
RUN apt-get update && apt-get install -y --no-install-recommends \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Create non‑root user (will be overridden by compose to run as root for Docker socket)
RUN groupadd -g 10001 hivebot && \
    useradd -u 10001 -g hivebot -m -s /bin/bash hivebot

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY backend/app ./app
COPY backend/scripts ./scripts

# Create secrets directory
RUN mkdir -p /opt/hivebot/secrets && \
    chown -R hivebot:hivebot /opt/hivebot

# Healthcheck using Python's built-in urllib (no extra dependencies)
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
