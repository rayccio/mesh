FROM python:3.11-slim
RUN pip install --no-cache-dir docker httpx playwright asyncssh
RUN playwright install chromium
COPY runner.py /runner.py
ENTRYPOINT ["python", "/runner.py"]
