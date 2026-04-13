from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
import os

load_dotenv()

DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t", "yes")

MAX_CALLS_PER_SESSION = int(os.getenv("MAX_CALLS_PER_SESSION", "5"))

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

STORAGE_ROOT_URL = os.getenv("STORAGE_ROOT_URL")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-unsafe-key-for-dev-only")

ALLOWED_HOSTS = [
    'yogacat-1058088277430.europe-west1.run.app',
    'yogacat.co.uk',
    'www.yogacat.co.uk',
    '127.0.0.1',
    'localhost',
    ]
ALLOWED_HOSTS = [host for host in ALLOWED_HOSTS if host]

LOGIN_REDIRECT_URL = '/'  # Redirect after successful login
LOGOUT_REDIRECT_URL = '/'  # Redirect after logout

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'whitenoise.runserver_nostatic',
    'website',
    'tinymce',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}




INTERNAL_IPS = [
    "127.0.0.1",
]

TINYMCE_DEFAULT_CONFIG = {
    'height': 300,
    'width': '100%',
    'menubar': True,
    'plugins': 'advlist autolink lists link image charmap print preview anchor',
    'toolbar': 'undo redo | formatselect | bold italic | alignleft aligncenter alignright | bullist numlist outdent indent | link image',
}  

MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'YogaCat.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "frontend/src/templates"], 
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



CSRF_TRUSTED_ORIGINS = [
    "http://*.sfl.local:8000",
    "http://localhost:5173",
    "https://*.sfl.ai",
    "https://le-330018731817.europe-west1.run.app"
]

WSGI_APPLICATION = 'YogaCat.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

USE_SSL_DB = os.getenv("DB_SSL", "true").lower() == "true"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.zpuraeylopsyzajkebly:{password}@aws-1-eu-west-2.pooler.supabase.com:5432/postgres".format(
        password=os.getenv("DB_PASSWORD")
    )
)

DATABASES = {
    'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=USE_SSL_DB)
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [os.path.join(BASE_DIR, "static/dist/assets")]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
