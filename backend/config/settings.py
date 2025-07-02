#backend/config/settings.py
import os
import dj_database_url
from pathlib import Path
from decouple import config
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PRICING_DATA_PATH = os.path.join(BASE_DIR, "backend", "logistics", "pricing_data")

# Environment
SECRET_KEY = config("SECRET_KEY", default="insecure-key")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost").split(",")

# Applications
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",

    # Local
    "logistics",
]

# Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Root URL config
ROOT_URLCONF = "config.urls"

# Templates
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# WSGI
WSGI_APPLICATION = "config.wsgi.application"

# Database
DATABASES = {
    "default": dj_database_url.parse(
        f"postgresql://{config('POSTGRES_USER')}:{config('POSTGRES_PASSWORD')}@"
        f"{config('POSTGRES_HOST')}:{config('POSTGRES_PORT')}/{config('POSTGRES_DB')}"
    ),
    "external": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("EXTERNAL_DB_NAME"),
        "USER": config("EXTERNAL_DB_USER"),
        "PASSWORD": config("EXTERNAL_DB_PASSWORD"),
        "HOST": config("EXTERNAL_DB_HOST"),
        "PORT": config("EXTERNAL_DB_PORT", default=5432, cast=int),
    }
}


# Redis 
REDIS_URL = config("REDIS_URL", default="redis://localhost:6379/0")

# Celery 
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"

# Cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Localization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static + media
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "frontend" / "dist",  
]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default PK
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# DRF settings
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}
