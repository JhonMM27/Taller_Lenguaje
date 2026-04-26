# ============================================================
# DOCKERFILE - Aplicacion Django para Produccion
# ============================================================
# Esta imagen usa python:3.11-slim para menor tamano.
# gunicorn sirve la aplicacion Django en lugar de runserver.
# ============================================================

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    fonts-dejavu-core \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libcairo2 \
    libjpeg62-turbo \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r base.txt

RUN useradd -m -u 1000 -s /bin/bash appuser

COPY --chown=appuser:appuser . .

RUN mkdir -p /app/staticfiles /app/media /etc/nginx/certs && \
    chown -R appuser:appuser /app/staticfiles /app/media /etc/nginx/certs && \
    chmod -R 755 /app && \
    find /app -type d -exec chmod g+ws {} \; && \
    find /app -type f -exec chmod g+rw {} \; && \
    chmod -R 777 /app/apps/*/migrations 2>/dev/null || true

RUN chmod +x /app/docker-entrypoint.sh

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]