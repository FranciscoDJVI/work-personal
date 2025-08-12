from pathlib import Path
import os
from dotenv import load_dotenv

# load file .env
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-sd#rn6vila6%1jgjboezdh=8*xy5^g)vc8q4ezzl#r0@0flr5t"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.humanize",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "psysmysql.apps.PsysmysqlConfig",
    "django_vite",
    "users",
    "phonenumber_field",
    "django_celery_results",
    # Django REST Framework
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "PsysMsql.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "PsysMsql.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "Psys",
        "USER": "root",
        "PASSWORD": os.environ.get("PASSWORD_BD"),
        "HOST": "localhost",
        "PORT": "3306",
        "OPTIONS": {"charset": "utf8mb4"},
    }
}

# Cache configuration
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://localhost:6379/1",  # Base 1 para cache (0 para Celery)
        "KEY_PREFIX": "psys_cache",
        "TIMEOUT": 300,  # 5 minutos por defecto
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"


USE_TZ: bool = True

TIME_ZONE = "America/Bogota"

USE_I18N = True



# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"
STATIFFILE_DIRS = [BASE_DIR / "assets"]

STATIC_ROOT = BASE_DIR / "staticfiles"
# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ADMIN-DASHBOARD
ADMIN_SITE_HEADER = "Dashboard"
ADMIN_SITE_TITLE = "Administrador"
ADMIN_HEADER = "Panel de control administrativo"

DJANGO_VITE = {"default": {"dev_mode": DEBUG}}

# REDIRECT URL SESION
LOGIN_REDIRECT_URL = "main"
LOGIN_URL = "accounts/login"
LOGOUT_URL = "logout"

# Configuración de Celery
CELERY_BROKER_URL = "redis://localhost:6379/0"  # URL de tu broker Redis
CELERY_RESULT_BACKEND = (
    "redis://localhost:6379/0"  # Donde se guardan los resultados de las tareas
)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "America/Bogota"  # O la zona horaria de tu proyecto
CELERY_TASK_TRACK_STARTED = True  # Opcional: Para saber cuando una tarea ha comenzado

# Configuración de Correo Electrónico (ajusta según tu proveedor)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"  # Ejemplo para Gmail
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "vanegasfrancisco415@gmail.com"  # Tu correo
EMAIL_HOST_PASSWORD = (
    "wzri cnjk gapz kxiw"  # Tu contraseña de aplicación (no la de la cuenta)
)
DEFAULT_FROM_EMAIL = "vanegasfrancisco415@gmail.com"
SERVER_EMAIL = "vanegasfrancisco415@gmail.com"

# ================================================================================
#                       DJANGO REST FRAMEWORK CONFIGURATION
# ================================================================================

from datetime import timedelta

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    },
    'EXCEPTION_HANDLER': 'psysmysql.api.exceptions.custom_exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=60),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React development server
    "http://127.0.0.1:3000",  # React development server
    "http://localhost:8000",  # Django development server
    "http://127.0.0.1:8000",  # Django development server
    "http://localhost:5173",  # Vite development server
    "http://127.0.0.1:5173",  # Vite development server
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# API Versioning
API_VERSION = 'v1'
API_BASE_URL = f'/api/{API_VERSION}/'

# ================================================================================
#                       DRF-SPECTACULAR CONFIGURATION
# ================================================================================

SPECTACULAR_SETTINGS = {
    'TITLE': 'PsysMsql API',
    'DESCRIPTION': 'API completa para el sistema de gestión de productos y ventas PsysMsql',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': False,
    'ENUM_NAME_OVERRIDES': {
        'ValidationErrorEnum': 'psysmysql.api.serializers.ValidationErrorEnum',
    },
    'POSTPROCESSING_HOOKS': [],
    'PREPROCESSING_HOOKS': [],
    'AUTHENTICATION_WHITELIST': [
        'psysmysql.api.authentication.CustomJWTAuthentication',
    ],
    'TAGS': [
        {'name': 'Authentication', 'description': 'Endpoints para autenticación y manejo de tokens'},
        {'name': 'Users', 'description': 'Gestión de usuarios del sistema'},
        {'name': 'Products', 'description': 'Gestión de productos del inventario'},
        {'name': 'Stock', 'description': 'Gestión de inventario y stock'},
        {'name': 'Clients', 'description': 'Gestión de clientes'},
        {'name': 'Sales', 'description': 'Gestión de ventas y transacciones'},
    ],
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
        'defaultModelsExpandDepth': 2,
        'defaultModelExpandDepth': 2,
        'displayRequestDuration': True,
        'docExpansion': 'none',
        'filter': True,
        'showExtensions': True,
        'showCommonExtensions': True,
    },
    'REDOC_UI_SETTINGS': {
        'hideDownloadButton': True,
        'expandResponses': '200',
        'pathInMiddlePanel': True,
        'nativeScrollbars': True,
    },
}

# Security for production
if not DEBUG:
    # CORS settings for production
    CORS_ALLOWED_ORIGINS = [
        # Add your production domains here
    ]
    
    # JWT settings for production
    SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(minutes=15)
    SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'] = timedelta(days=1)
