FROM hivebot/bridge-base:latest

# Copy Discord bridge implementation
COPY backend/bridges/discord.py /app/bridges/discord.py

# Install Discord dependencies
RUN pip install discord.py==2.3.2

CMD ["python", "-m", "bridges.worker"]
