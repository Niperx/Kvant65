"""
Production settings for Render (PostgreSQL, WhiteNoise).
Use: DJANGO_SETTINGS_MODULE=kvant_site.settings.production
"""
import os
import dj_database_url
from .base import *

DEBUG = False

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required in production")

ALLOWED_HOSTS = [
    ".onrender.com",
    ".render.com",
]
_render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if _render_host:
    ALLOWED_HOSTS.append(_render_host)
_extra_hosts = os.environ.get("ALLOWED_HOSTS", "").strip()
if _extra_hosts:
    ALLOWED_HOSTS.extend(h.strip() for h in _extra_hosts.split(",") if h.strip())

# БД: PostgreSQL если задан DATABASE_URL, иначе SQLite из репо (для демо)
_database_url = os.environ.get("DATABASE_URL")
if _database_url:
    DATABASES = {
        "default": dj_database_url.config(
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
    # Медиа из репо — раздаём Django (только для демо/показа)
    SERVE_MEDIA = True

# WhiteNoise — раздача статики без отдельного сервера
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# URL сайта для Wagtail (админка, письма). Render задаёт RENDER_EXTERNAL_HOSTNAME
_base_url = os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("WAGTAILADMIN_BASE_URL")
if _base_url:
    WAGTAILADMIN_BASE_URL = _base_url.rstrip("/")
else:
    _host = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "example.onrender.com")
    WAGTAILADMIN_BASE_URL = f"https://{_host}"

# Медиа: S3 при заданных переменных, иначе локальная папка (на Render эфемерно)
_use_s3 = os.environ.get("AWS_STORAGE_BUCKET_NAME")
if _use_s3:
    INSTALLED_APPS = list(INSTALLED_APPS) + ["storages"]
    # Постоянное хранилище медиа на Render
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
    AWS_STORAGE_BUCKET_NAME = _use_s3
    AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "us-east-1")
    AWS_S3_CUSTOM_DOMAIN = os.environ.get("AWS_S3_CUSTOM_DOMAIN", "")
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
    AWS_DEFAULT_ACL = "public-read"
    AWS_LOCATION = "media"  # префикс в бакете: media/...
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    if AWS_S3_CUSTOM_DOMAIN:
        MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/media/"
    else:
        MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/media/"
else:
    MEDIA_ROOT = BASE_DIR / "media"
    MEDIA_URL = "/media/"
