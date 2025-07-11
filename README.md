# logistic-app-2.0

A Django + Django REST Framework backend with Celery workers and Redis for processing and comparing shipping invoices against internal order data. Generates Google Sheets exports and Slack notifications for out‐of‐threshold deltas.

## Table of Contents

- [Features](#features)  
- [Tech Stack](#tech-stack)  
- [Prerequisites](#prerequisites)  
- [Getting Started](#getting-started)  
  - [1. Clone Repo](#1-clone-repo)  
  - [2. Backend Setup](#2-backend-setup)  
  - [3. Frontend Setup](#3-frontend-setup)  
- [Configuration](#configuration)  
  - [Environment Variables](#environment-variables)  
  - [Django Settings](#django-settings)  
  - [Celery & Redis](#celery--redis)  
- [Running Locally](#running-locally)  
  - [Via Docker Compose](#via-docker-compose)  
  - [Manually](#manually)  
- [API Reference](#api-reference)  
- [Slack Integration](#slack-integration)  
- [Google Sheets Export](#google-sheets-export)  
- [Deployment](#deployment)  
- [Contributing](#contributing)  
- [License](#license)

## Features

- **Invoice Parsing** for multiple courier partners (Brenger, Libero, Sw De Vries, Wuunder)  
- **Delta Calculation**: flagging shipments where invoice > expected price  
- **Celery Workers** for background processing (pipeline: load → evaluate → export)  
- **Slack Bot**: automatically reacts to invoice posts in a channel  
- **Google Sheets** export via service account, with conditional formatting  

## Tech Stack

- **Python 3.12**, **Django 4.2**, **Django REST Framework**  
- **Celery** for asynchronous tasks  
- **Redis** as broker & result backend  
- **PostgreSQL** (via SQLAlchemy for external DB access)  
- **Docker** / **Docker Compose** for containerization  
- **Gunicorn** production WSGI server  
- **Slack SDK** for notifications  
- **gspread** for Google Sheets integration  

## Prerequisites

- Docker & Docker Compose (or Python 3.12 + Redis + Postgres locally)  
- Google service account JSON (for Sheets API)  
- Slack Bot Token & Channel ID  

## Getting Started

### 1. Clone Repo

```bash
git clone https://github.com/whoppah/logistic-app-2.0.git
cd logistic-app-2.0
````

### 2. Backend Setup

```bash
cd backend
cp .env.example .env
# Edit .env to add real secrets (DATABASE_URL, EXTERNAL_DB_*, REDIS_URL, SECRET_KEY, SLACK_*, GOOGLE_SERVICE_ACCOUNT_FILE, etc.)
docker build -t logistics-backend .
```

### 3. Frontend Setup

> *Coming soon…* (Your React/Vue/Next.js frontend lives in `/frontend`.)

## Configuration

### Environment Variables

Copy `backend/.env.example` to `.env` and set:

| Variable                          | Description                                    |
| --------------------------------- | ---------------------------------------------- |
| `SECRET_KEY`                      | Django secret key                              |
| `DEBUG`                           | `True` for dev, `False` for prod               |
| `DATABASE_URL`                    | Primary DB URL (for Django)                    |
| `EXTERNAL_DB_NAME`, `_USER`, etc. | Credentials for external orders database       |
| `REDIS_URL`                       | e.g. `redis://localhost:6379/0`                |
| `SLACK_BOT_TOKEN`                 | xoxb-… bot token                               |
| `SLACK_CHANNEL_ID`                | C123… channel where invoices are posted        |
| `GOOGLE_SERVICE_ACCOUNT_FILE`     | Path to JSON credentials for Google Sheets API |

### Django Settings

* Configured in `backend/config/settings.py`
* CORS origin set to your frontend URL

### Celery & Redis

* Broker & backend both point at `REDIS_URL`
* Workers launched via `entrypoint.sh worker`
* Beat scheduler via `entrypoint.sh beat`

## Running Locally

### Via Docker Compose

```yaml
version: "3.8"
services:
  redis:
    image: redis:7
  backend:
    build: ./backend
    command: ./entrypoint.sh web
    ports:
      - "8000:8000"
    environment:
      - DEBUG=True
      - REDIS_URL=redis://redis:6379/0
      # other env vars…
    volumes:
      - ./backend:/app
    depends_on:
      - redis
  worker:
    build: ./backend
    command: ./entrypoint.sh worker
    environment: *backend_env
    depends_on:
      - backend
      - redis
  beat:
    build: ./backend
    command: ./entrypoint.sh beat
    environment: *backend_env
    depends_on:
      - backend
      - redis
```

```bash
docker-compose up --build
```

### Manually

1. Create & activate a Python venv
2. `pip install -r requirements.txt`
3. `python manage.py migrate && python manage.py collectstatic --noinput`
4. In one terminal: `./entrypoint.sh web`
5. In another: `./entrypoint.sh worker`

## API Reference

All endpoints are prefixed with `/logistics/`:

| Path                 | Method | Description                        |
| -------------------- | ------ | ---------------------------------- |
| `/upload/`           | POST   | Upload invoice file(s)             |
| `/check-delta/`      | POST   | Kick off delta pipeline            |
| `/task-status/`      | GET    | Poll for Celery task status        |
| `/task-result/`      | GET    | Retrieve pipeline result           |
| `/analytics/`        | GET    | Summary stats over recent runs     |
| `/pricing/metadata/` | GET    | Get pricing‐list file metadata     |
| `/pricing/`          | POST   | Lookup pricing data in DB          |
| `/slack/messages/`   | GET    | List recent Slack channel messages |
| `/slack/threads/`    | GET    | Fetch a thread by timestamp        |
| `/slack/react/`      | POST   | Add/remove reaction on a message   |

## Slack Integration

* Posts in the configured channel with “Partner: brenger/libero/…”
* Bot auto-reacts ✔️ or ❌ based on delta check
* Downloads attachments and triggers Celery pipeline

## Google Sheets Export

* Each partner has its own worksheet: `Sheet_brenger`, `Sheet_libero`, etc.
* New rows appended with headers on first run
* Positive deltas are highlighted in yellow

## Deployment

We deploy via Railway (or Heroku/DigitalOcean):

* **Procfile**:

  ```
  web:    ./entrypoint.sh web
  worker: ./entrypoint.sh worker
  beat:   ./entrypoint.sh beat
  ```
* Set environment vars in your deployment dashboard.
* Attach a managed Redis add-on.

## Contributing

1. Fork & create feature branch
2. Run tests & lint (`pytest`, `flake8`)
3. Submit a PR against `main`

## License

MIT © Your Company Name

```
---  

**Next steps:**  
- Verify your `.env` keys & secrets.  
- Add the frontend README once your UI is in place.  
- Adjust any partner-specific parser notes or pricing-data paths as needed.
```
