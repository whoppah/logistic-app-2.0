FROM python:3.12-slim

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
# Expose port
EXPOSE 8000

# Run Gunicorn using the correct path to the WSGI application
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
