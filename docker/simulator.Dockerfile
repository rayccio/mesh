FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY simulator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY simulator/ ./simulator/

CMD ["python", "-m", "simulator.main"]
