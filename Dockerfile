FROM python:3.10-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src ./src
COPY app.py api.py stream_transcribe.py .

# Create and use a non-root user
RUN useradd -m appuser
USER appuser

CMD ["python", "app.py"]
