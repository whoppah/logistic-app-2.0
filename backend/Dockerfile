# Use an official Python image as base
FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install OS dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip \
 && pip install -r requirements.txt

# Copy the entire project into the container
COPY . /app/

# Ensure your Google service-account JSON lands in the right path
COPY backend/logistics/pricing_data /app/backend/logistics/pricing_data

# Add and make executable the entrypoint
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose the port that Gunicorn will bind to
EXPOSE 8000

# Default to running the Django web server; 
# Procfile defines web/worker/beat for Railway
CMD ["/app/entrypoint.sh", "web"]
