FROM hivebot/bridge-base:latest

# Copy WhatsApp bridge implementation
COPY backend/bridges/whatsapp.py /app/bridges/whatsapp.py

# Install WhatsApp dependencies (e.g., twilio)
RUN pip install twilio==8.10.0

CMD ["python", "-m", "bridges.worker"]
