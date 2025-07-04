# Dockerfile (from your project root)
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# system deps
RUN apt-get update && apt-get install -y \
    build-essential libpq-dev curl \
  && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# your code
COPY . .

COPY logistics/pricing_data /app/logistics/pricing_data

# entrypoint + permissions
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

EXPOSE 8000
CMD ["./entrypoint.sh", "web"]
