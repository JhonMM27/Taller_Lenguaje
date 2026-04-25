from .base import *
import os

DEBUG = True

DATABASE_URL = os.getenv('DATABASE_URL', '')

if DATABASE_URL and DATABASE_URL.startswith('postgres'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': DATABASE_URL.split('/')[-1].split('?')[0],
            'USER': 'dev_user',
            'PASSWORD': 'dev_pass_2026',
            'HOST': 'db',
            'PORT': '5432',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

INSTALLED_APPS = [a for a in INSTALLED_APPS if a != 'debug_toolbar']
MIDDLEWARE = [m for m in MIDDLEWARE if m != 'whitenoise.middleware.WhiteNoiseMiddleware']

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'