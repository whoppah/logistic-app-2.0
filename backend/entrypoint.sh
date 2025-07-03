#!/usr/bin/env bash
set -e

case "$1" in

  web)
    echo "🛠️  Applying database migrations..."
    python manage.py migrate
    echo "🧹 Collecting static files..."
    python manage.py collectstatic --noinput

    echo "🚀 Starting Gunicorn web server..."
    exec gunicorn config.wsgi:application \
      --bind 0.0.0.0:${PORT:-8000} \
      --workers 2 \
      --timeout 120 \
      --log-level info
    ;;

  worker)
    echo "🕵️‍♂️ Starting Celery worker..."
    exec celery -A config.celery_app worker --loglevel=info
    ;;

  beat)
    echo "⏰ Starting Celery beat..."
    exec celery -A config.celery_app beat --loglevel=info
    ;;

  *)
    echo "Usage: $0 {web|worker|beat}"
    exit 1
    ;;

esac
