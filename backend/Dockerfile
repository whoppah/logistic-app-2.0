FROM python:3.12-slim

WORKDIR /logistic-app-2.0/backend

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the full backend code
COPY backend .

# Expose port
EXPOSE 8000

# Run Gunicorn using the correct path to the WSGI application
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
