# backend/Dockerfile
FROM python:3.12-slim

# 2) Env
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 3) OS deps
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
  && rm -rf /var/lib/apt/lists/*

# 4) Python deps
COPY requirements.txt /app/
RUN pip install --upgrade pip \
 && pip install -r requirements.txt

# 5) Copy backend code
COPY . /app/

# 6) Ensure pricing_data dir exists and copy the JSON
RUN mkdir -p /app/logistics/pricing_data
COPY logistics/pricing_data/upbeat-flame-451212-j5-8d545d206f5e.json \
     /app/logistics/pricing_data/

# 7) Entrypoint
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# 8) Expose Gunicorn port
EXPOSE 8000

# 9) Default to web
CMD ["/app/entrypoint.sh", "web"]
