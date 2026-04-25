#!/bin/bash
# ============================================================
# ENTRYPOINT - Script de inicio del contenedor Django
# ============================================================
# Este script se ejecuta automaticamente al iniciar el contenedor.
# Espera a que PostgreSQL este disponible, ejecuta migraciones,
# crea el superusuario si no existe, y arranca Gunicorn.
# ============================================================

# --------------------------------------------------
# Conversion CRLF a LF (compatibilidad Windows)
# --------------------------------------------------
# Si el archivo fue creado en Windows con finales de linea CRLF,
# los convierte a LF para evitar errores de sintaxis en Linux.
if file "$0" 2>/dev/null | grep -q "CRLF"; then
    echo "Convirtiendo finales de linea Windows (CRLF) a Unix (LF)..."
    sed -i 's/\r$//' "$0"
    echo "Conversion completada. Continuando..."
fi

# --------------------------------------------------
# Manejo de errores
# --------------------------------------------------
# 'set -e' hace que el script salga inmediatamente si
# algun comando falla. Esto previene errores silenciosos.
set -e

echo "============================================"
echo "Iniciando aplicacion Django..."
echo "============================================"

# --------------------------------------------------
# Esperar a que PostgreSQL este disponible
# --------------------------------------------------
# PostgreSQL puede tardar en inicializar, especialmente
# la primera vez que crea la base de datos.
# Intentamos hasta 90 veces (90 * 2s = 3 minutos maximo)
MAX_RETRIES=90
RETRY_COUNT=0

# Obtener credenciales de variables de entorno
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
        echo "Revisa que el contenedor de postgres este corriendo."
        echo "Comando intentado:"
        echo "  psql -h $DB_HOST -U $DB_USER -d $DB_NAME"
        exit 1
    fi
    echo "Intento $RETRY_COUNT/$MAX_RETRIES - esperando 2 segundos..."
    sleep 2
done

echo "=== PostgreSQL esta listo! ==="

# --------------------------------------------------
# Ejecutar migraciones de Django
# --------------------------------------------------
# Crea/actualiza las tablas de la base de datos
echo "Ejecutando migraciones..."
python manage.py migrate --noinput

# --------------------------------------------------
# Recolectar archivos estaticos
# --------------------------------------------------
# Copia todos los archivos estaticos (CSS, JS) a STATIC_ROOT
# para que Nginx pueda servirlos directamente
echo "Recolectando archivos estaticos..."
rm -rf /app/staticfiles/* 2>/dev/null || true
python manage.py collectstatic --noinput

# --------------------------------------------------
# Crear superusuario si no existe
# --------------------------------------------------
# Solo crea si no existe un usuario con ese email
# Usa variables de entorno para credenciales
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
echo "  - pgAdmin:    http://localhost:5050"
echo ""
echo "============================================"

# --------------------------------------------------
# Ejecutar Gunicorn
# --------------------------------------------------
# Gunicorn sirve la aplicacion Django en produccion.
# Mas info: config/settings/production.py
exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    config.wsgi:application
