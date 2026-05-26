"""Django settings for InsightHub."""

import os
import sys
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

try:
    import dj_database_url
except ImportError:
    dj_database_url = None

BASE_DIR = Path(__file__).resolve().parent.parent


def load_env_file(path):
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file(BASE_DIR / ".env")


def env_bool(name, default="False"):
    return os.getenv(name, default).lower() == "true"


def env_list(name, default=""):
    return [value.strip() for value in os.getenv(name, default).split(",") if value.strip()]

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "" if os.getenv("RENDER") else "django-insecure-assignment-only-change-me-in-development",
)
DEBUG = env_bool("DEBUG", "False")
IS_PRODUCTION = not DEBUG

if IS_PRODUCTION and (
    not SECRET_KEY
    or SECRET_KEY.startswith("django-insecure-")
    or SECRET_KEY == "django-insecure-assignment-only-change-me-in-production"
):
    raise ImproperlyConfigured("A strong SECRET_KEY is required when DEBUG=False.")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
if IS_PRODUCTION and not ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS must be set when DEBUG=False.")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "storages",
    "apps.core",
    "apps.ingestion",
    "apps.validation_service.apps.ValidationServiceConfig",
    "apps.review",
    "apps.audit.apps.AuditConfig",
    "apps.dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "InsightHub.urls"

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

WSGI_APPLICATION = "InsightHub.wsgi.application"

AUTH_USER_MODEL = "core.User"

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and dj_database_url:
    conn_max_age = int(os.getenv("DB_CONN_MAX_AGE", "0"))
    db_schema = os.getenv("DB_SCHEMA", "").strip()
    is_postgres_url = DATABASE_URL.startswith(("postgres://", "postgresql://"))
    DATABASES = {
        "default": dj_database_url.config(
            conn_max_age=conn_max_age,
            conn_health_checks=True,
            ssl_require=is_postgres_url and os.getenv("DB_SSL_REQUIRE", "True").lower() == "true",
        )
    }
    if is_postgres_url and "pooler.supabase.com" in DATABASE_URL:
        DATABASES["default"].setdefault("OPTIONS", {})
        DATABASES["default"]["OPTIONS"]["prepare_threshold"] = None
    if is_postgres_url and db_schema:
        DATABASES["default"].setdefault("OPTIONS", {})
        DATABASES["default"]["OPTIONS"]["options"] = f"-c search_path={db_schema}"
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

USE_LOCAL_MEDIA_STORAGE = env_bool("USE_LOCAL_MEDIA_STORAGE")
USE_S3_STORAGE = env_bool("USE_S3_STORAGE", "True") and not USE_LOCAL_MEDIA_STORAGE

if USE_LOCAL_MEDIA_STORAGE:
    STORAGES["default"] = {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    }
else:
    AWS_ACCESS_KEY_ID = os.getenv("SUPABASE_S3_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("SUPABASE_S3_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("SUPABASE_S3_BUCKET")
    AWS_S3_ENDPOINT_URL = os.getenv("SUPABASE_S3_ENDPOINT_URL")
    AWS_S3_REGION_NAME = os.getenv("SUPABASE_S3_REGION", "us-east-1")
    AWS_S3_SIGNATURE_VERSION = "s3v4"
    AWS_S3_ADDRESSING_STYLE = "path"
    AWS_QUERYSTRING_AUTH = True
    AWS_DEFAULT_ACL = None
    missing_s3_settings = [
        name
        for name, value in {
            "SUPABASE_S3_ACCESS_KEY_ID": AWS_ACCESS_KEY_ID,
            "SUPABASE_S3_SECRET_ACCESS_KEY": AWS_SECRET_ACCESS_KEY,
            "SUPABASE_S3_BUCKET": AWS_STORAGE_BUCKET_NAME,
            "SUPABASE_S3_ENDPOINT_URL": AWS_S3_ENDPOINT_URL,
        }.items()
        if not value
    ]
    if missing_s3_settings:
        raise ImproperlyConfigured(f"Missing S3 settings: {', '.join(missing_s3_settings)}")
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
    }

UPLOAD_MAX_BYTES = int(os.getenv("UPLOAD_MAX_BYTES", str(10 * 1024 * 1024)))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REDIS_URL = os.getenv("REDIS_URL")
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "insighthub-local-cache",
        }
    }

CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL") or REDIS_URL or "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND") or CELERY_BROKER_URL
if CELERY_BROKER_URL.startswith("rediss://") and "ssl_cert_reqs=" not in CELERY_BROKER_URL:
    CELERY_BROKER_URL = f"{CELERY_BROKER_URL}?ssl_cert_reqs=CERT_NONE"
if CELERY_RESULT_BACKEND.startswith("rediss://") and "ssl_cert_reqs=" not in CELERY_RESULT_BACKEND:
    CELERY_RESULT_BACKEND = f"{CELERY_RESULT_BACKEND}?ssl_cert_reqs=CERT_NONE"
CELERY_TASK_ALWAYS_EAGER = env_bool(
    "CELERY_TASK_ALWAYS_EAGER",
    "True" if DEBUG else "False",
) or "test" in sys.argv

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

if IS_PRODUCTION:
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", "True")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", "True")
    SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", "True")
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}

CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    "" if IS_PRODUCTION else "http://localhost:5173,http://127.0.0.1:5173",
)
if IS_PRODUCTION and not CORS_ALLOWED_ORIGINS:
    raise ImproperlyConfigured("CORS_ALLOWED_ORIGINS must be set when DEBUG=False.")

CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")
