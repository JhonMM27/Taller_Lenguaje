# ============================================================
# CONFIGURACION DE PRODUCCION
# ============================================================
# Configuracion para despliegue en Docker con PostgreSQL.
# Esta configuracion es leida cuando DJANGO_SETTINGS_MODULE
# esta establecido como config.settings.production
# ============================================================
from .base import *
import os

# ============================================================
# MODO DEBUG
# ============================================================
# En produccion DEBUG debe ser SIEMPRE False
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# ============================================================
# CLAVE SECRETA
# ============================================================
# Obtenida de variable de entorno (nunca hardcodear en produccion)
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    # Levanta error si no hay clave secreta configurada
    raise ValueError(
        "SECRET_KEY no esta configurada. "
        "Define la variable SECRET_KEY en el archivo .env de produccion."
    )

# ============================================================
# HOSTS PERMITIDOS
# ============================================================
# Permite acceso desde cualquier host en desarrollo Docker
# Para produccion con dominio real, cambiar a ['tudominio.com']
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,host.docker.internal').split(',')

# ============================================================
# CONFIGURACION DE BASE DE DATOS POSTGRESQL
# ============================================================
# Lee las variables de entorno definidas en docker-compose.yml
# y configura la conexion a PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        # Nombre de la base de datos (creada por postgres en docker-compose)
        'NAME': os.getenv('POSTGRES_DB', 'facturacion_db'),
        # Usuario de PostgreSQL
        'USER': os.getenv('POSTGRES_USER', 'sunat_user'),
        # Password de PostgreSQL
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
        # Host = nombre del servicio en docker-compose
        'HOST': 'postgres',
        # Puerto por defecto de PostgreSQL
        'PORT': '5432',
        # Configuracion de conexion optimizada para Docker
        'CONN_MAX_AGE': 60,           # Mantiene conexiones vivas por 60s
        'OPTIONS': {
            'connect_timeout': 10,    # Timeout de conexion en segundos
        },
    }
}

# ============================================================
# SEGURIDAD DE COOKIES Y SESSIONS
# ============================================================
# Estas configuraciones aseguran que las cookies sean seguras
# cuando se usa HTTPS en produccion
CSRF_COOKIE_SECURE = True     # Solo envia cookie CSRF por HTTPS
SESSION_COOKIE_SECURE = True  # Solo envia cookie de sesion por HTTPS
SECURE_SSL_REDIRECT = os.getenv('FORCE_HTTPS', 'False') == 'True'

# Cookie de sesion httponly (previene acceso via JavaScript)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 86400    # 24 horas

# ============================================================
# ARCHIVOS ESTATICOS (WhiteNoise)
# ============================================================
# WhiteNoise permite a Django servir archivos estaticos eficientemente
# sin necesidad de un servidor web adicional para ellos.
# STATIC_ROOT es donde collectstatic recoge los archivos.
MIDDLEWARE = [
    # WhiteNoise debe estar cerca del inicio, despues de SessionMiddleware
    'whitenoise.middleware.WhiteNoiseMiddleware',
] + [m for m in MIDDLEWARE if m not in [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]]

# Storage para archivos estaticos
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# ============================================================
# CORS (Cross-Origin Resource Sharing)
# ============================================================
# Permite que el frontend (si hay) acceda a la API
# En produccion, limitar a tu dominio de frontend
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://localhost",
    "https://127.0.0.1",
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://localhost",
    "https://127.0.0.1",
]

# ============================================================
# LOGGING PARA PRODUCCION
# ============================================================
# En produccion, solo logueamos warnings y errores para reducir
# el tamano de los logs y mejorar rendimiento
LOGGING['root']['level'] = 'WARNING'

# Agregar loggers específicos si no existen
if 'loggers' not in LOGGING:
    LOGGING['loggers'] = {}

LOGGING['loggers']['django'] = {
    'level': 'WARNING',
    'handlers': ['console'],
    'propagate': False,
}

# ============================================================
# REST FRAMEWORK
# ============================================================
# Configuracion para API REST en produccion
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # Throttling para evitar abusos (5 usuarios maximo)
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '100/hour',  # 100 requests por hora por usuario
    },
}
