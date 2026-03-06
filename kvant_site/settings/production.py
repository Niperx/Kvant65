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

# PostgreSQL from Render (DATABASE_URL)
DATABASES = {
    "default": dj_database_url.config(
        conn_max_age=600,
        conn_health_checks=True,
    )
}

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

# На Render файловая система эфемерная — загруженные медиа пропадут при редеплое.
# Для постоянного хранения медиа позже можно подключить S3 или аналог.
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"
