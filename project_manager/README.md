# Intelligent Collaborative Project Management System

A Django project management system with collaboration features and analytics.

## Requirements
- Python 3.11+
- PostgreSQL (recommended) or SQLite (development)

## Setup

### 1) Create virtual environment
```bat
cd "c:/Users/ASUS/Desktop/6th sem prj/project/project_manager"
python -m venv venv
venv\Scripts\activate
```

### 2) Install dependencies
```bat
pip install -r requirements.txt
```

### 3) Configure environment variables
1. Copy `.env` from the template (already present in the project root).
2. Set these values:
- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- PostgreSQL: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`
- `DB_ENGINE=postgres` (or `sqlite`)

### 4) Database migrations
```bat
python manage.py makemigrations
python manage.py migrate
```

### 5) Run server
```bat
python manage.py runserver
```

## API base URL
- Swagger is not configured by default.
- REST endpoints are under: `/api/`

## Deployment (Render/Railway)
This repo includes:
- `Procfile`
- `runtime.txt`

Deployments should set environment variables including database credentials.

## Notes
- For static files, use WhiteNoise when deploying.
- WebSockets are configured with Channels (Redis required for production websocket messaging).

