#!/bin/bash
# ============================================================
# Script para generar certificado SSL autofirmado
# ============================================================
# Este script crea un certificado SSL autofirmado para HTTPS
# en desarrollo local. NO usar en produccion con usuarios reales.
#
# Uso: ./scripts/generate_ssl.sh
# ============================================================

set -e  # Sale si hay error

# Directorio donde se guardaran los certificados
CERTS_DIR="$(pwd)/certs"

echo "============================================"
echo "Generando certificados SSL autofirmados..."
echo "============================================"

# Crear directorio de certificados si no existe
mkdir -p "$CERTS_DIR"

# Generar clave privada RSA de 2048 bits
# -aes256: encripta la clave con AES-256 (pedira contrasena)
# -out: archivo de salida
openssl genrsa -out "$CERTS_DIR/ca.key" 4096 2>/dev/null

# Generar certificado CA raiz autofirmado
# -x509: genera certificado auto-firmado en formato X.509
# -days 3650: valido por 10 anos
# -sha256: usa algoritmo SHA-256 para firmar
openssl req -x509 -new -nodes -sha256 -days 3650 \
    -key "$CERTS_DIR/ca.key" \
    -out "$CERTS_DIR/ca.crt" \
    -subj "/C=PE/ST=Lima/L=Lima/O=Development/CN=Local-CA" 2>/dev/null

# Generar clave privada para el servidor
openssl genrsa -out "$CERTS_DIR/server.key" 2048 2>/dev/null

# Generar CSR (Certificate Signing Request)
# Esto crea una solicitud de firma que luego firmaremos con nuestra CA
openssl req -new -sha256 \
    -key "$CERTS_DIR/server.key" \
    -out "$CERTS_DIR/server.csr" \
    -subj "/C=PE/ST=Lima/L=Lima/O=Development/CN=localhost" 2>/dev/null

# Archivo de configuracion para extensiones de certificado
# Define que el certificado es para servidor (Server Authentication)
cat > "$CERTS_DIR/server_ext.cnf" << EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = host.docker.internal
IP.1 = 127.0.0.1
IP.2 = 0.0.0.0
EOF

# Firmar el CSR con nuestra CA
# -CA: usa el certificado CA para firmar
# -CAkey: clave privada de la CA
# -CAserial: archivo con el numero de serie para el certificado
openssl x509 -req -sha256 -days 3650 \
    -in "$CERTS_DIR/server.csr" \
    -CA "$CERTS_DIR/ca.crt" \
    -CAkey "$CERTS_DIR/ca.key" \
    -out "$CERTS_DIR/server.crt" \
    -extfile "$CERTS_DIR/server_ext.cnf" \
    -CAcreateserial 2>/dev/null

# Copiar certificado del servidor a la ubicacion que usa Nginx
cp "$CERTS_DIR/server.crt" /etc/nginx/certs/server.crt 2>/dev/null || true
cp "$CERTS_DIR/server.key" /etc/nginx/certs/server.key 2>/dev/null || true

# Limpiar archivos temporales
rm -f "$CERTS_DIR/server.csr" "$CERTS_DIR/server_ext.cnf"

echo ""
echo "============================================"
echo "Certificados generados exitosamente!"
echo "============================================"
echo ""
echo "Archivos creados en: $CERTS_DIR/"
echo "  - ca.crt      : Certificado CA (importar en navegador)"
echo "  - ca.key      : Clave privada CA (NO compartir)"
echo "  - server.crt  : Certificado del servidor"
echo "  - server.key  : Clave privada del servidor"
echo ""
echo "Para usar HTTPS:"
echo "1. Importa 'certs/ca.crt' en tu navegador como CA confiable"
echo "   (o simplemente acepta el certificado autofirmado)"
echo "2. Accede a https://localhost"
echo ""
