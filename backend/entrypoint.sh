#!/usr/bin/env bash
set -e

# Default to “web” if no arg given
if [ -z "$1" ]; then
  set -- web
fi

case "$1" in
  web)
    python manage.py migrate
    python manage.py collectstatic --noinput

    echo "🚀 Starting Gunicorn on port ${PORT:-8000}"
    exec gunicorn config.wsgi:application \
      --bind 0.0.0.0:"${PORT:-8000}" \
      --workers 2 \
      --timeout 120 \
      --log-level info
    ;;
  worker)
    exec celery -A config.celery_app worker --loglevel=info
    ;;
  beat)
    exec celery -A config.celery_app beat --loglevel=info
    ;;
  *)
    echo "Usage: $0 {web|worker|beat}"
    exit 1
    ;;
esac
