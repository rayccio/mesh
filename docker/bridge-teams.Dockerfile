FROM hivebot/bridge-base:latest

# Copy Microsoft Teams bridge implementation
COPY backend/bridges/teams.py /app/bridges/teams.py

# Install Teams dependencies (e.g., botbuilder)
RUN pip install botbuilder-core==4.15.0

CMD ["python", "-m", "bridges.worker"]
