# backend/Dockerfile
FROM python:3.12-slim

# Avoid .pyc files, unbuffered I/O
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # so your exporter can find the JSON key
    GOOGLE_SERVICE_ACCOUNT_FILE=/app/logistics/pricing_data/upbeat-flame-451212-j5-8d545d206f5e.json

WORKDIR /app

# 1) OS dependencies
RUN apt-get update \
 && apt-get install -y build-essential libpq-dev curl \
 && rm -rf /var/lib/apt/lists/*

# 2) Python dependencies
# requirements.txt lives alongside manage.py in backend/
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install -r requirements.txt

# 3) Copy *all* of your Django project (including pricing_data)
COPY . .

# 4) Entrypoint
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

EXPOSE 8000

# Default to launching the web process
CMD ["./entrypoint.sh", "web"]
