# ============================================================
# SETTINGS.PY — Configuración principal del proyecto
# Stack validado: Django 4.2.8 + DRF 3.14.0 + Python 3.13
# ============================================================

import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# SEGURIDAD
# ============================================================
SECRET_KEY    = os.getenv('SECRET_KEY', 'clave-insegura-solo-para-desarrollo')
DEBUG         = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# ============================================================
# APLICACIONES
# ============================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Librerías de terceros
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',
    'corsheaders',
    'drf_spectacular',

    # Apps del proyecto
    'estudiantes',
    'ranking',
    'plazas',
]

# ============================================================
# MIDDLEWARE
# RequestMiddleware PRIMERO para capturar usuario e IP
# en cualquier operación save() de ModelBase
# ============================================================
MIDDLEWARE = [
    'helpers.middleware.RequestMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'internado.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'internado.wsgi.application'

# ============================================================
# BASE DE DATOS — PostgreSQL
# Contenedor Docker: postgres:16.2
# ============================================================
DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql',
        'NAME':     os.getenv('DB_NAME',     'internado_db'),
        'USER':     os.getenv('DB_USER',     'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST':     os.getenv('DB_HOST',     'localhost'),
        'PORT':     os.getenv('DB_PORT',     '5432'),
        'OPTIONS': {
            'options': '-c search_path=public,core,academico,estudiantil,practicas,ia'
        },
    }
}
# ============================================================
# CACHÉ — Redis
# Contenedor Docker: redis:7.2
# Usado para caché y rate limiting de auth_helper.py
# ============================================================
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
    }
}

# ============================================================
# AUTENTICACIÓN JWT — SimpleJWT 5.3.0
# Tokens leídos desde cookies HttpOnly (protección XSS)
# ============================================================
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':  timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS':    True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_COOKIE':           'access_token',
    'AUTH_COOKIE_REFRESH':   'refresh_token',
    'AUTH_COOKIE_HTTP_ONLY': True,
    'AUTH_COOKIE_SECURE':    not DEBUG,
    'AUTH_COOKIE_SAMESITE':  'Lax',
    'ALGORITHM':             'HS256',
    'SIGNING_KEY':           SECRET_KEY,
    'AUTH_HEADER_TYPES':     ('Bearer',),
}

# ============================================================
# DJANGO REST FRAMEWORK
# ============================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    # Paginación LimitOffset — 25 registros (estándar ERP)
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 25,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter',
        'rest_framework.filters.SearchFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# ============================================================
# DOCUMENTACIÓN — drf-spectacular 0.27.0
# ============================================================
SPECTACULAR_SETTINGS = {
    'TITLE':       'API — Sistema de Internado Preprofesional',
    'DESCRIPTION': 'API REST con XGBoost para asignación prioritaria de plazas.',
    'VERSION':     '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# ============================================================
# CORS — permite peticiones desde el frontend
# ============================================================
CORS_ALLOWED_ORIGINS = os.getenv(
    'CORS_ALLOWED_ORIGINS', 'http://localhost:3000'
).split(',')
CORS_ALLOW_CREDENTIALS = True

# ============================================================
# INTERNACIONALIZACIÓN — Estándar ERP Ecuador
# ============================================================
LANGUAGE_CODE = 'es-ec'
TIME_ZONE     = 'America/Guayaquil'
USE_I18N      = True
USE_TZ        = True

# ============================================================
# ESTÁTICOS
# ============================================================
STATIC_URL         = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================
# LOGGING — registra errores del sistema en consola
# ============================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detallado': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style':  '{',
        },
    },
    'handlers': {
        'consola': {
            'class':     'logging.StreamHandler',
            'formatter': 'detallado',
        },
    },
    'root': {
        'handlers': ['consola'],
        'level':    'WARNING',
    },
}
