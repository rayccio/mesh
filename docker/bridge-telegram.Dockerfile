FROM hivebot/bridge-base:latest

# Copy the Telegram bridge implementation
COPY backend/bridges/telegram.py /app/bridges/telegram.py

# Install Telegram-specific dependencies
RUN pip install python-telegram-bot==20.7

CMD ["python", "-m", "bridges.worker"]
