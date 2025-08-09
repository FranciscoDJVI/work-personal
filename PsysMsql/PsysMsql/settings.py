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
]

MIDDLEWARE = [
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


USE_TZ = True

TIME_ZONE = "America/Bogota"

USE_I18N = True

USE_TZ = True


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

