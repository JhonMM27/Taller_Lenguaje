# Sistema de Facturación Electrónica SUNAT - Perú

Sistema de facturación electrónica desarrollado en Django para cumplir con las regulaciones de SUNAT/OSE en Perú. Genera comprobantes (Facturas, Boletas, Notas de Crédito) en formato UBL 2.1, listos para envío a operadores certificados.

---

## 📋 Índice

- [Requisitos](#-requisitos)
- [Instalación Rápida](#-instalación-rápida)
- [Configuración de Variables de Entorno](#-configuración-de-variables-de-entorno)
- [Ejecutar con Docker](#-ejecutar-con-docker)
- [Nuevas Funcionalidades](#-nuevas-funcionalidades)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Flujo de Comprobantes](#-flujo-de-comprobantes)
- [API REST](#-api-rest)
- [Configuración SUNAT/OSE](#-configuración-sunatose)
- [Credenciales de Acceso](#-credenciales-de-acceso)
- [Resolución de Problemas](#-resolución-de-problemas)

---

## 🔧 Requisitos

- Docker y Docker Compose
- Python 3.11+ (para desarrollo local sin Docker)
- Git
- OpenSSL (para generar certificados SSL)

---

## 🚀 Instalación Rápida

### 1. Clonar o descargar el proyecto

```bash
cd "tu_directorio"
```

### 2. Generar certificados SSL

```bash
# Crear directorio de certificados
mkdir -p certs

# Generar certificado autofirmado (Linux/Mac)
openssl req -x509 -newkey rsa:2048 -keyout certs/server.key -out certs/server.crt -days 365 -nodes -subj "/C=PE/ST=Lima/L=Lima/O=SUNAT/CN=localhost" -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

# En Windows (PowerShell):
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -keyout certs/server.key -out certs/server.crt -days 365 -nodes -subj "/C=PE/ST=Lima/L=Lima/O=SUNAT/CN=localhost" -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
```

### 3. Levantar con Docker

```bash
docker compose up -d --build
```

> **Nota:** El entrypoint ejecuta automáticamente: espera PostgreSQL, crea migraciones, aplica migraciones, recolecta estáticos y crea superusuario.

### 4. Acceder a la aplicación

- **Aplicación:** http://localhost
- **HTTPS:** https://localhost (aceptar certificado autofirmado)
- **pgAdmin:** http://localhost:5051

---

## ⚙️ Configuración de Variables de Entorno

### Archivo `.env` (raíz del proyecto)

```env
# Modo desarrollo: True = Mock OSE, False = OSE real
SUNAT_OSE_MOCK=True

# Solo llenar cuando SUNAT_OSE_MOCK=False
SUNAT_OSE_WSDL=https://e-beta.sunat.gob.pe/ol-ti-itcpe/billService
SUNAT_OSE_RUC=20512345671
SUNAT_OSE_USUARIO=tu_usuario
SUNAT_OSE_PASSWORD=tu_password

# Certificado digital para firma XML
SUNAT_CERT_PATH=/path/a/certificado.pfx
SUNAT_CERT_PASSWORD=password_certificado
```

---

## 🐳 Ejecutar con Docker

### Levantar todos los servicios

```bash
docker compose up -d --build
```

### Detener servicios

```bash
docker compose down
```

### Detener y eliminar volúmenes (limpieza completa)

```bash
docker compose down -v
```

### Ver logs

```bash
docker compose logs -f
docker compose logs backend --tail=50
```

### Reiniciar backend

```bash
docker compose restart backend
```

---

## 🆕 Nuevas Funcionalidades

### 1. Categorías de Productos

Gestión de categorías para clasificar productos según su tipo.

**Acceso:** `/productos/categorias/`

| Campo | Descripción |
|-------|-------------|
| Nombre | Nombre de la categoría |
| Código SUNAT | Código de bien/servicio según SUNAT |
| Descripción | Descripción opcional |
| Activa | Si está activa para uso |

**Operaciones:** Crear, Editar, Eliminar, Listar

---

### 2. Tipo de Operación en Productos

Clasificación tributaria de productos según tipo de operación.

**Acceso:** Crear/Editar producto (`/productos/nuevo/` o `/productos/editar/{id}/`)

| Tipo de Operación | Código UBL | Descripción |
|-------------------|------------|-------------|
| Gravada | 10, 11, 14, 15 | Operaciones con IGV |
| Exonerada | 20 | Operaciones exentas de IGV |
| Inafecta | 30, 31, 32, 36 | Operaciones no gravadas |
| Gratuita | 21 | Operaciones gratuitas |
| Exportación | 40 | Exportación de bienes/servicios |

**Ejemplo:** Productos farmacéuticos pueden ser "Exonerada" (20) para el sector salud.

---

### 3. Importar Comprobantes desde CSV

Importación masiva de comprobantes usando archivo CSV.

**Acceso:** `/comprobantes/importar/`

**Formato del archivo CSV (delimitador: `;`):**

```csv
tipo;serie;numero;fecha;cliente_tipo_doc;cliente_num_doc;cliente_nombre;producto_codigo;producto_descripcion;cantidad;precio_unitario;categoria
01;F001;1;2026-04-25;6;20123456789;Empresa ABC S.A.;MED001;Paracetamol 500mg;10;15.50;FARMACIA
01;F001;2;2026-04-25;6;20123456789;Empresa ABC S.A.;MED002;Ibuprofeno 400mg;5;22.00;FARMACIA
03;B001;1;2026-04-25;1;12345678;Juan Perez;CON001;Consulta médica;1;80.00;CONSULTAS
```

| Columna | Descripción | Ejemplo |
|---------|-------------|---------|
| tipo | 01=Factura, 03=Boleta | 01 |
| serie | Serie del documento | F001 |
| numero | Número correlativo | 1 |
| fecha | Fecha (YYYY-MM-DD) | 2026-04-25 |
| cliente_tipo_doc | 6=RUC, 1=DNI | 6 |
| cliente_num_doc | Número de documento | 20123456789 |
| cliente_nombre | Nombre o razón social | Empresa ABC S.A. |
| producto_codigo | Código del producto | MED001 |
| producto_descripcion | Descripción del producto | Paracetamol 500mg |
| cantidad | Cantidad | 10 |
| precio_unitario | Precio unitario | 15.50 |
| categoria | Nombre de categoría (opcional) | FARMACIA |

**Funcionalidades:**
- Crea automáticamente clientes si no existen
- Crea automáticamente productos si no existen
- Crea categorías automáticamente si no existen
- Registra errores de importación

---

### 4. Envío Masivo de Comprobantes

Envío de múltiples comprobantes en un solo lote.

**Acceso:** `/sunat_ose/envio-masivo/`

**Flujo:**
1. Seleccionar comprobantes con checkboxes (estado BORRADOR o EMITIDO)
2. Hacer clic en "Enviar Lote"
3. El sistema genera un ZIP con todos los XML
4. Envía usando método `send_pack` del OSE
5. Registra ticket para seguimiento

**Límites:**
- Máximo 1000 documentos por lote (según规范 SUNAT)
- Todos los documentos deben tener la misma fecha de emisión

**Historial:**
- Ver lotes enviados anteriormente
- Estado: PENDIENTE, PROCESANDO, COMPLETADO, ERROR
- Ticket OSE para seguimiento

---

## 📁 Estructura del Proyecto

```
proyecto_final/
├── apps/
│   ├── empresas/          # CRUD de empresas
│   ├── clientes/          # CRUD de clientes
│   ├── productos/        # CRUD de productos, categorías
│   ├── comprobantes/     # Facturas, boletas, notas, importación CSV
│   ├── notas_credito/     # Notas de crédito
│   ├── sunat_ose/         # Integración SUNAT/OSE, envío masivo
│   ├── reportes/          # Reportes y dashboards
│   └── usuarios/          # Autenticación
├── config/
│   ├── settings/
│   │   ├── base.py        # Configuración base
│   │   ├── local.py       # Desarrollo
│   │   └── production.py  # Producción (PostgreSQL)
│   └── urls.py            # Rutas principales
├── templates/             # Templates HTML
├── certs/                 # Certificados SSL
├── nginx/                 # Configuración Nginx
├── scripts/               # Scripts de utilidad
├── docs/                  # Documentación SUNAT
├── docker-compose.yml     # Configuración Docker
├── Dockerfile             # Imagen del backend
├── docker-entrypoint.sh   # Script de inicio
├── .env                   # Variables de entorno (NO commitear)
└── README.md
```

---

## 📊 Flujo de Comprobantes

El sistema implementa el flujo completo de un comprobante electrónico:

```
┌──────────┐     Emitir      ┌──────────┐   Enviar a SUNAT   ┌──────────┐   Consultar Ticket   ┌──────────┐
│ BORRADOR │ ────────────→  │ EMITIDO  │ ────────────────→  │  ENVIADO │ ──────────────────→  │ ACEPTADO │
└──────────┘                └──────────┘                    └──────────┘                      └──────────┘
                                                                       │
                                                                       │ (10% probabilidad)
                                                                       ↓
                                                                  RECHAZADO
                                                                       │
                                                                  [Reenviar]
```

### Estados del Comprobante

| Estado | Descripción |
|--------|-------------|
| `BORRADOR` | Creado, sin XML generado |
| `EMITIDO` | XML generado, listo para enviar |
| `ENVIADO` | Enviado al OSE, esperando respuesta |
| `ACEPTADO` | Confirmado por SUNAT |
| `RECHAZADO` | Error devuelto por el OSE |

---

## 🔌 API REST

### Endpoints Principales

| Método | URL | Descripción |
|--------|-----|-------------|
| POST | `/api/auth/login/` | Iniciar sesión |
| GET | `/api/facturas/` | Listar facturas |
| POST | `/api/facturas/` | Crear factura |
| GET | `/api/comprobantes/` | Listar comprobantes |
| POST | `/api/comprobantes/importar/` | Importar desde CSV |
| GET | `/api/comprobantes/{id}/` | Ver comprobante |
| POST | `/api/ose/comprobante/{id}/enviar/` | Enviar a SUNAT |
| POST | `/api/ose/comprobante/{id}/consultar/` | Consultar ticket |
| GET | `/api/productos/categorias/` | Listar categorías |
| GET | `/api/reportes/dashboard/` | Dashboard stats |

### Autenticación

```bash
# Login
curl -X POST http://localhost/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@prueba.com", "password": "admin"}'
```

---

## 🔐 Configuración SUNAT/OSE

### Modo Mock (Desarrollo)

Por defecto, `SUNAT_OSE_MOCK=True`. El sistema usa `MockOSEClient` que:
- Simula 90% aceptación, 10% rechazo
- Genera tickets falsos
- No conecta a SUNAT real
- Ideal para probar el flujo completo

### Modo Producción (OSE Real)

1. Contratar con un OSE certificador (SUNAT, SUMAQ, otros)
2. Obtener credenciales y WSDL
3. Editar `.env`:
```env
SUNAT_OSE_MOCK=False
SUNAT_OSE_WSDL=https://e-beta.sunat.gob.pe/ol-ti-itcpe/billService
SUNAT_OSE_RUC=20512345671
SUNAT_OSE_USUARIO=usuario_ose
SUNAT_OSE_PASSWORD=password_ose
```

---

## 👤 Credenciales de Acceso

| Servicio | Email | Password | URL |
|----------|-------|----------|-----|
| Django Admin | admin@prueba.com | admin | http://localhost/admin |
| pgAdmin | admin@sunat.local.com | admin123 | http://localhost:5051 |

---

## 🔧 Resolución de Problemas

### Puerto 5432 ya en uso (PostgreSQL local)

```bash
# Detener PostgreSQL local
docker stop sunat_postgres
docker compose down
docker compose up -d
```

### Regenerar certificado SSL

```bash
openssl req -x509 -newkey rsa:2048 -keyout certs/server.key -out certs/server.crt -days 365 -nodes -subj "/C=PE/ST=Lima/L=Lima/O=SUNAT/CN=localhost" -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
docker compose restart nginx
```

### Cambiar contraseña del admin

```bash
docker compose exec backend python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
u = User.objects.get(email='admin@prueba.com')
u.set_password('nueva_contrasena')
u.save()
"
```

### Ver estado de migraciones

```bash
docker compose exec backend python manage.py showmigrations
```

### Forzar recrear migraciones

```bash
docker compose exec backend python manage.py makemigrations --force
```

---

## 📚 Recursos

- [Documentación SUNAT](docs/)
- [Manual técnico OSE v5](docs/Manual%20tecnico%20de%20operatividad%20OSE%20v5/)

---

**Versión:** 2.0.0  
**Última actualización:** Abril 2026