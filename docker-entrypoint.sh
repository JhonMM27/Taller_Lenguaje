#!/bin/bash
set -e

echo "============================================"
echo "Iniciando aplicacion Django..."
echo "============================================"

MAX_RETRIES=90
RETRY_COUNT=0

DB_HOST=${POSTGRES_HOST:-postgres}
DB_USER=${POSTGRES_USER:-sunat_user}
DB_NAME=${POSTGRES_DB:-facturacion_db}
DB_PASS=${POSTGRES_PASSWORD:-sunat_pass_2026}

echo "Esperando a PostgreSQL en $DB_HOST..."
echo "Base de datos: $DB_NAME"

until PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" >/dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo ""
        echo "ERROR: PostgreSQL no esta disponible despues de $MAX_RETRIES intentos."
        exit 1
    fi
    echo "Intento $RETRY_COUNT/$MAX_RETRIES - esperando 2 segundos..."
    sleep 2
done

echo "=== PostgreSQL esta listo! ==="

# ==============================================================================
# SECCIÓN: CONFIGURACIÓN DE PERMISOS PARA IMPORTACIONES Y MEDIOS
# ==============================================================================
# Nos aseguramos de que el directorio de subidas exista físicamente y tenga
# todos los permisos de lectura y escritura para el usuario appuser.
echo "Asegurando la carpeta de importaciones y permisos de medios..."
mkdir -p /app/media/importaciones 2>/dev/null || true
chmod -R 777 /app/media 2>/dev/null || true

echo "Asegurando permisos en carpetas de migraciones..."
find /app -type d -name migrations -exec chmod -R 777 {} \; 2>/dev/null || true
mkdir -p /app/apps/*/migrations 2>/dev/null || true

echo "Creando migraciones si hay modelos nuevos..."
python manage.py makemigrations --noinput || true

echo "Ejecutando migraciones..."
python manage.py migrate --noinput

echo "Recolectando archivos estaticos..."
rm -rf /app/staticfiles/* 2>/dev/null || true
python manage.py collectstatic --noinput

echo "Verificando superusuario..."
python manage.py shell -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
admin_email = os.environ.get('DJANGO_ADMIN_EMAIL', 'admin@prueba.com')
admin_pass = os.environ.get('DJANGO_ADMIN_PASSWORD', 'admin')
if not User.objects.filter(email=admin_email).exists():
    User.objects.create_superuser('admin', admin_email, admin_pass)
    print(f'Superusuario creado: {admin_email}')
else:
    print(f'Superusuario ya existe: {admin_email}')
print(f'Total usuarios en el sistema: {User.objects.count()}')
"

echo "============================================"
echo "Iniciando Gunicorn en puerto 8000..."
echo "============================================"
echo ""
echo "Accesos disponibles:"
echo "  - Aplicacion: http://localhost (o https://localhost)"
echo "  - pgAdmin:    http://localhost:5051"
echo ""
echo "============================================"

exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    config.wsgi:application