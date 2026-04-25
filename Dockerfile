# ============================================================
# DOCKERFILE - Aplicacion Django para Produccion
# ============================================================
# Esta imagen usa python:3.11-slim para menor tamano.
# gunicorn sirve la aplicacion Django en lugar de runserver.
# ============================================================

# --------------------------------------------------
# Imagen base: Python 3.11 (version slim = mas pequena)
# --------------------------------------------------
FROM python:3.11-slim

# --------------------------------------------------
# Variables de entorno
# --------------------------------------------------
# Evita que Python cree archivos .pyc
ENV PYTHONDONTWRITEBYTECODE=1
# Muestra logs de Docker en tiempo real
ENV PYTHONUNBUFFERED=1

# --------------------------------------------------
# Configuracion de directorio de trabajo
# --------------------------------------------------
WORKDIR /app

# --------------------------------------------------
# Instalacion de dependencias del sistema
# --------------------------------------------------
# libs necesarias para:
# - build-essential, libpq-dev: compilacion psycopg2 y otras deps
# - libxml2-dev, libxslt1-dev: para lxml (parsing XML SOAP SUNAT)
# - fonts-dejavu-core, etc: para WeasyPrint (generacion PDF)
RUN apt-get update && apt-get install -y \
    # Herramientas de compilacion
    build-essential \
    libpq-dev \
    # Librerias para XML/SOAP (SUNAT)
    libxml2-dev \
    libxslt1-dev \
    # Librerias para generacion de PDF (WeasyPrint)
    fonts-dejavu-core \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libcairo2 \
    libjpeg62-turbo \
    # Cliente PostgreSQL (para migraciones y comandos)
    postgresql-client \
    # cleanup
    && rm -rf /var/lib/apt/lists/*

# --------------------------------------------------
# Instalacion de dependencias Python
# --------------------------------------------------
# Copia solo el archivo de requirements primero (para cache de Docker)
COPY requirements/base.txt .

# Actualiza pip e instala dependencias
# --no-cache-dir: no guarda cache de pip (imagen mas pequena)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r base.txt

# --------------------------------------------------
# Creacion de usuario no-root
# --------------------------------------------------
# Por seguridad, no ejecutamos como root
# El usuario 1000 es el standard de Docker
RUN useradd -m -u 1000 -s /bin/bash appuser && \
    chown -R appuser:appuser /app

# --------------------------------------------------
# Archivos de la aplicacion
# --------------------------------------------------
# Copia todo el codigo al contenedor
COPY --chown=appuser:appuser . .

# --------------------------------------------------
# Permisos de directorios
# --------------------------------------------------
# Django necesita escribir en estos directorios
RUN mkdir -p /app/staticfiles /app/media && \
    chown -R appuser:appuser /app/staticfiles /app/media

# --------------------------------------------------
# Hacer ejecutable el entrypoint
# --------------------------------------------------
RUN chmod +x /app/docker-entrypoint.sh

# --------------------------------------------------
# Directorio para certificados SSL
# --------------------------------------------------
RUN mkdir -p /etc/nginx/certs && \
    chown -R appuser:appuser /etc/nginx/certs

# --------------------------------------------------
# Cambio a usuario no-root
# --------------------------------------------------
USER appuser

# --------------------------------------------------
# Exposicion de puerto
# --------------------------------------------------
# Gunicorn escucha en este puerto
EXPOSE 8000

# --------------------------------------------------
# Punto de entrada - usa docker-entrypoint.sh
# --------------------------------------------------
# El entrypoint espera PostgreSQL, hace migrate,
# collectstatic, crea superuser, y ejecuta Gunicorn
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# --------------------------------------------------
# Comando por defecto (ignorado si hay ENTRYPOINT)
# --------------------------------------------------
# Solo se usa si ENTRYPOINT no esta definido
#CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "2", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "config.wsgi:application"]
