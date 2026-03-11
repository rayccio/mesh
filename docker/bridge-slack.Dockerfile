FROM hivebot/bridge-base:latest

# Copy Slack bridge implementation
COPY backend/bridges/slack.py /app/bridges/slack.py

# Install Slack dependencies
RUN pip install slack-sdk==3.21.3

CMD ["python", "-m", "bridges.worker"]
