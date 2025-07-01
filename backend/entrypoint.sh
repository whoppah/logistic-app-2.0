#!/bin/bash
set -e

echo "Applying database migrations..."
python manage.py migrate
python manage.py collectstatic --noinput

# Start Gunicorn with increased timeout and multiple workers
echo "Starting Gunicorn server..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 120 \
    --log-level info
    
