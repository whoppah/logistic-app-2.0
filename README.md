# Logistic-app-2.0

A full-stack logistics dashboard:

- **Backend**: Django + DRF, Celery workers & Redis, PostgreSQL (via SQLAlchemy), Slack & Google Sheets integrations  
- **Frontend**: React + Vite + Tailwind CSS, with dynamic file upload, polling of Celery tasks, pricing lookups, Slack thread browser & analytics charts  

## Table of Contents

- [Features](#features)  
- [Tech Stack](#tech-stack)  
- [Getting Started](#getting-started)  
  - [1. Clone Repo](#1-clone-repo)  
  - [2. Backend Setup](#2-backend-setup)  
  - [3. Frontend Setup](#3-frontend-setup)  
- [Configuration](#configuration)  
  - [Environment Variables](#environment-variables)  
  - [Django Settings](#django-settings)  
  - [Vite & Tailwind](#vite--tailwind)  
  - [Celery & Redis](#celery--redis)  
- [Running Locally](#running-locally)  
  - [Via Docker Compose](#via-docker-compose)  
  - [Manually](#manually)  
- [API Reference](#api-reference)  
- [Slack Integration](#slack-integration)  
- [Google Sheets Export](#google-sheets-export)  
- [Deployment](#deployment)  
---

## Features

- **Invoice Parsing** for multiple courier partners (Brenger, Libero, Sw De Vries, Wuunder, Transpoksi (to be implemented), MagicMovers (to be implemented), Tadde)  
- **Delta Calculation** with customizable threshold  
- **Asynchronous Pipeline**: load → evaluate → export via Celery  
- **Slack Bot**: auto-reacts to invoice posts and threads in the private channel 'invoices-logistics'
- **Google Sheets** export with conditional formatting based on Delta>Threshold (~ 20 $)
- **Dashboard UI**: upload invoices and view delta table in 'Invoice Dashboard', pricing lookup in 'Pricing', Slack thread browser (not yet connected with the main dashboard) & 'Analytics'

## Tech Stack

- **Backend**  
  - Python 3.12, Django 4.2, Django REST Framework  
  - Celery, Redis, PostgreSQL (SQLAlchemy), Gunicorn  
  - Slack SDK, gspread (Google Sheets API)  
- **Frontend**  
  - React 18, Vite, Tailwind CSS  
  - Axios, React Router, Recharts, Lucide icons  

---

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
# Edit .env with your secrets: DATABASE_URL, EXTERNAL_DB_*, REDIS_URL, SECRET_KEY, SLACK_BOT_TOKEN, SLACK_CHANNEL_ID, GOOGLE_SERVICE_ACCOUNT_FILE, etc.
docker build -t logistics-backend .
```

### 3. Frontend Setup

```bash
cd frontend
cp .env.example .env   # see Environment Variables below
npm install
npm run dev
```

---

## Configuration

### Environment Variables

#### Backend (`backend/.env`)

| Variable                                                   | Description                                      |
| ---------------------------------------------------------- | ------------------------------------------------ |
| `SECRET_KEY`                                               | Django secret key                                |
| `DEBUG`                                                    | `True` for dev, `False` for prod                 |
| `DATABASE_URL`                                             | e.g. `postgres://user:pass@host:5432/dbname`     |
| `EXTERNAL_DB_NAME`, `_USER`, `_PASSWORD`, `_HOST`, `_PORT` | External orders DB credentials                   |
| `REDIS_URL`                                                | e.g. `redis://localhost:6379/0`                  |
| `SLACK_BOT_TOKEN`                                          | xoxb-…                                           |
| `SLACK_CHANNEL_ID`                                         | C123…                                            |
| `GOOGLE_SERVICE_ACCOUNT_FILE`                              | Path to your service-account JSON for Sheets API |

#### Frontend (`frontend/.env`)

```env
VITE_API_URL=http://localhost:8000
```

### Django Settings

* `backend/config/settings.py` reads from your `.env`
* CORS is configured to allow your frontend origin

### Vite & Tailwind

* **`vite.config.js`** proxies `/api` to your Django server
* **`tailwind.config.js`** extends colors, fonts & includes forms/typography/aspect-ratio plugins
* Global styles in `src/index.css` apply your design system

### Celery & Redis

* Broker & result backend both use `REDIS_URL`
* Tasks launched via `./entrypoint.sh worker` 

---

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
    env_file:
      - backend/.env
    volumes:
      - ./backend:/app
    depends_on:
      - redis
  worker:
    build: ./backend
    command: ./entrypoint.sh worker
    env_file:
      - backend/.env
    depends_on:
      - backend
      - redis
  beat:
    build: ./backend
    command: ./entrypoint.sh beat
    env_file:
      - backend/.env
    depends_on:
      - backend
      - redis
  frontend:
    image: node:18
    working_dir: /app/frontend
    volumes:
      - ./frontend:/app/frontend
    command: sh -c "npm install && npm run dev"
    ports:
      - "3000:3000"
    env_file:
      - frontend/.env
```

```bash
docker-compose up --build
```

### Manually

1. **Backend**

   ```bash
   cd backend
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py collectstatic --noinput
   ./entrypoint.sh web
   ./entrypoint.sh worker   # in another terminal
   ```
2. **Frontend**

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

## API Reference

All endpoints under `/logistics/` (or `/api/logistics/` if you remap in Vite):

| Path                 | Method | Description                         |
| -------------------- | ------ | ----------------------------------- |
| `/upload/`           | POST   | Upload invoice file(s)              |
| `/check-delta/`      | POST   | Start delta pipeline (202 → celery) |
| `/task-status/`      | GET    | Poll Celery task status             |
| `/task-result/`      | GET    | Retrieve pipeline result            |
| `/analytics/`        | GET    | Dashboard usage & delta trends      |
| `/pricing/metadata/` | GET    | Get available routes & categories   |
| `/pricing/`          | GET    | Lookup partner pricing by route/cat |
| `/slack/messages/`   | GET    | Fetch recent Slack messages         |
| `/slack/threads/`    | GET    | Fetch replies for a thread          |
| `/slack/react/`      | POST   | Add/remove reaction on a message    |

---

## Slack Integration

* Listens for messages with `Partner: <key>` and attached invoice files
* Downloads files, enqueues Celery pipeline, reacts ✔️ or 🟥 based on delta

## Google Sheets Export

* Each partner gets its own worksheet (e.g. `Sheet_brenger`)
* Appends new rows, highlights positive Δ in yellow
* Shared to your service-account’s configured email

---

## Deployment

We deploy via Railway.
