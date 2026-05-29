"""
<<<<<<< HEAD
GPD.AI — Django Settings
=======
GPDetect — Django Settings
>>>>>>> 1cd9214f7b497c4ad019fd155e3b385cffbdc6f0
Backend for Plagiarism Detection System
"""

import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

import environ
env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

<<<<<<< HEAD
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-GPD-dev-key-change-in-production')
=======
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-GPD-dev-key-change-in-production') # fallback for development, must be set in production in env 
>>>>>>> 1cd9214f7b497c4ad019fd155e3b385cffbdc6f0

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
DJANGO_BASE_URL = os.getenv("DJANGO_BASE_URL", "http://localhost:8000")

<<<<<<< HEAD
# ── Applications ─────────────────────────────────────────────────────────────
=======
# Applications 
>>>>>>> 1cd9214f7b497c4ad019fd155e3b385cffbdc6f0
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
<<<<<<< HEAD
]
=======
] 
>>>>>>> 1cd9214f7b497c4ad019fd155e3b385cffbdc6f0
THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
]
LOCAL_APPS = [
    'apps.accounts',
    'apps.plans',
    'apps.workspaces',
    'apps.submissions',
    'apps.results',
]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

<<<<<<< HEAD
MIDDLEWARE = [
=======
MIDDLEWARE = [ 
>>>>>>> 1cd9214f7b497c4ad019fd155e3b385cffbdc6f0
    'corsheaders.middleware.CorsMiddleware',          # Must be first
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
<<<<<<< HEAD
]
=======
] 
>>>>>>> 1cd9214f7b497c4ad019fd155e3b385cffbdc6f0

ROOT_URLCONF = 'GPD_Back.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
<<<<<<< HEAD
}]

WSGI_APPLICATION = 'GPD_Back.wsgi.application'

# ── Database ─────────────────────────────────────────────────────────────────
_is_ci = os.environ.get('CI', 'false').lower() == 'true'
DATABASES = {
    # ── SQLite (development) ──────────────────────────────────
    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': BASE_DIR / 'db.sqlite3',
    # }

    # ── SQL Server (production) ───────────────────────────────
    # pip install mssql-django
=======
}] 

WSGI_APPLICATION = 'GPD_Back.wsgi.application'

# Database  
_is_ci = os.environ.get('CI', 'false').lower() == 'true'
DATABASES = {
>>>>>>> 1cd9214f7b497c4ad019fd155e3b385cffbdc6f0
    'default': {
        'ENGINE':   os.environ.get('DB_ENGINE', 'mssql'),
        'NAME':     os.environ.get('DB_NAME', 'GPD'),
        'HOST':     os.environ.get('DB_HOST', r'DESKTOP-OJ5AKU2\SQLEXPRESS'),
        'PORT':     os.environ.get('DB_PORT', ''),
        'USER':     os.environ.get('DB_USER', ''),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'OPTIONS': {
            'driver': os.environ.get('DB_ODBC_DRIVER', 'ODBC Driver 18 for SQL Server'),
            'extra_params': 'TrustServerCertificate=yes;Encrypt=yes;' if _is_ci else '',
        },
    }
<<<<<<< HEAD

    # ── PostgreSQL (alternative) ──────────────────────────────
    # pip install psycopg2-binary
    # 'default': {
    #     'ENGINE': 'django.db.backends.postgresql',
    #     'NAME': os.environ.get('DB_NAME', 'GPD_db'),
    #     'USER': os.environ.get('DB_USER', 'GPD_user'),
    #     'PASSWORD': os.environ.get('DB_PASSWORD', ''),
    #     'HOST': os.environ.get('DB_HOST', 'localhost'),
    #     'PORT': os.environ.get('DB_PORT', '5432'),
    # }
}

# ── Custom User Model ─────────────────────────────────────────────────────────
AUTH_USER_MODEL = 'accounts.User'

# ── Password Validation ───────────────────────────────────────────────────────
=======
}

# Custom User Model 
AUTH_USER_MODEL = 'accounts.User' 

# Password Validation 
>>>>>>> 1cd9214f7b497c4ad019fd155e3b385cffbdc6f0
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
<<<<<<< HEAD
]

# ── Internationalization ──────────────────────────────────────────────────────
=======
] 

# Internationalization 
>>>>>>> 1cd9214f7b497c4ad019fd155e3b385cffbdc6f0
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

<<<<<<< HEAD
# ── Static & Media ───────────────────────────────────────────────────────────
=======
# Static & Media 
>>>>>>> 1cd9214f7b497c4ad019fd155e3b385cffbdc6f0
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

<<<<<<< HEAD
# ── Django REST Framework ─────────────────────────────────────────────────────
=======
# Django REST Framework
>>>>>>> 1cd9214f7b497c4ad019fd155e3b385cffbdc6f0
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
<<<<<<< HEAD
}

# ── JWT Configuration ─────────────────────────────────────────────────────────
=======
} 

# JWT Configuration 
>>>>>>> 1cd9214f7b497c4ad019fd155e3b385cffbdc6f0
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

<<<<<<< HEAD
# ── CORS ─────────────────────────────────────────────────────────────────────
=======
# CORS 
>>>>>>> 1cd9214f7b497c4ad019fd155e3b385cffbdc6f0
# Development: allow all origins
CORS_ALLOW_ALL_ORIGINS = DEBUG

# Production: set explicit origins
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",    # React dev server
    "http://127.0.0.1:3000",
    "https://GPD.example.com",  # Production URL
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = [
    'DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT',
]
CORS_ALLOW_HEADERS = [
    'accept', 'accept-encoding', 'authorization', 'content-type',
    'dnt', 'origin', 'user-agent', 'x-csrftoken', 'x-requested-with',
]

<<<<<<< HEAD
# ── File Upload Settings ──────────────────────────────────────────────────────
ALLOWED_DOCUMENT_EXTENSIONS = ['.pdf', '.docx', '.doc', '.txt']
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB

# ── Plan Limits ───────────────────────────────────────────────────────────────
=======
# File Upload Settings 
ALLOWED_DOCUMENT_EXTENSIONS = ['.pdf', '.docx', '.doc', '.txt']
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB

# Plan Limits
>>>>>>> 1cd9214f7b497c4ad019fd155e3b385cffbdc6f0
PLAN_DEFAULTS = {
    'Starter':    {'checks': 10,  'max_sources': 5,  'max_docs': 3},
    'Pro':        {'checks': 50,  'max_sources': 20, 'max_docs': 10},
    'Enterprise': {'checks': -1,  'max_sources': -1, 'max_docs': -1},
}

CELERY_BROKER_URL    = os.environ.get('CELERY_BROKER_URL', 'amqp://localhost')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'rpc://')
CELERY_TASK_SERIALIZER = 'json'

<<<<<<< HEAD
# ── Storage Microservice ──────────────────────────────────────────────────────
STORAGE_SERVICE_URL = os.environ.get('STORAGE_SERVICE_URL', '')

# ── AI Model ──────────────────────────────────────────────────────────────────
=======
# Storage Microservice 
STORAGE_SERVICE_URL = os.environ.get('STORAGE_SERVICE_URL', '')

# AI Model
>>>>>>> 1cd9214f7b497c4ad019fd155e3b385cffbdc6f0
AI_MODEL_URL = os.environ.get('AI_MODEL_URL', '')

# ── Email Configuration ───────────────────────────────────────────────────────
# For development: prints emails to the console instead of sending them
# Change to smtp backend + credentials for production

EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    #'django.core.mail.backends.console.EmailBackend'   # dev: prints to terminal
     'django.core.mail.backends.smtp.EmailBackend'    # prod: real email
)
# Gmail SMTP example (set in environment variables, never hardcode):
EMAIL_HOST          = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT          = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = os.environ.get('EMAIL_HOST_USER', '')      # your@gmail.com
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')  # Gmail app password
DEFAULT_FROM_EMAIL  = os.environ.get('DEFAULT_FROM_EMAIL', 'GPD.AI <engtalaalkhateeb2004@gmail.com>')
'''
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')  
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')  

DEFAULT_FROM_EMAIL = f'GPD.AI <{EMAIL_HOST_USER}>'
SERVER_EMAIL = EMAIL_HOST_USER

'''
<<<<<<< HEAD

# ── AUTH_USER_MODEL: point to Account (base model) ───────────────────────────
# Keep this as 'accounts.User' because that's what the migration named it.
# The proxy models (User, Admin) share this table.
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
=======
>>>>>>> 1cd9214f7b497c4ad019fd155e3b385cffbdc6f0
