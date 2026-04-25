# Sistema de Facturación Electrónica SUNAT - Perú

Sistema de facturación electrónica desarrollado en Django para cumplir con las regulaciones de SUNAT/OSE en Perú. Genera comprobantes (Facturas, Boletas, Notas de Crédito) en formato UBL 2.1, listos para envío a operadores certificados.

---

## 📋 Índice

- [Requisitos](#-requisitos)
- [Instalación Rápida](#-instalación-rápida)
- [Configuración de Variables de Entorno](#-configuración-de-variables-de-entorno)
- [Ejecutar con Docker](#-ejecutar-con-docker)
- [Ejecutar sin Docker (Local)](#-ejecutar-sin-docker-local)
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

---

## 🚀 Instalación Rápida

### 1. Clonar o descargar el proyecto

```bash
cd "tu_directorio"
```

### 2. Crear archivo .env

```bash
cp .env.example .env
```

### 3. Levantar con Docker

```bash
docker-compose up --build
```

¡Listo! Accede a http://localhost:8000

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
docker-compose up --build
```

> **Nota:** `docker-compose up --build` rebuild la imagen pero las migraciones se ejecutan automáticamente en el entrypoint.

### Detener servicios

```bash
docker-compose down
```

### Ver logs

```bash
docker-compose logs -f
```

### Reiniciar backend

```bash
docker-compose restart backend
```

### Acceso a la aplicación

- **URL:** http://localhost:8000
- **Admin:** http://localhost:8000/admin

---

## 📦 Migraciones

### Con Docker

```bash
# Ver estado de migraciones
docker-compose exec backend python manage.py showmigrations

# Ejecutar migraciones pendientes
docker-compose exec backend python manage.py migrate

# Crear migraciones (después de modificar modelos)
docker-compose exec backend python manage.py makemigrations

# Forzar aplicarlas
docker-compose exec backend python manage.py migrate --noinput
```

### Sin Docker (Local)

```bash
# Ver estado
python manage.py showmigrations

# Ejecutar
python manage.py migrate

# Crear
python manage.py makemigrations
```

### Resetear base de datos

```bash
# Borra la base y crea nuevas migraciones
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

---

## 💻 Ejecutar sin Docker (Local)

### 1. Crear entorno virtual

```bash
python -m venv venv
```

### 2. Activar entorno virtual

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements/base.txt
```

### 4. Configurar base de datos SQLite

El proyecto usa SQLite por defecto cuando no hay `DATABASE_URL` con PostgreSQL.

### 5. Ejecutar migraciones

```bash
python manage.py migrate
```

### 6. Crear superusuario

```bash
python manage.py createsuperuser
```

### 7. Ejecutar servidor

```bash
python manage.py runserver
```

---

## 📁 Estructura del Proyecto

```
proyecto_final/
├── apps/
│   ├── empresas/          # CRUD de empresas/empresas
│   ├── clientes/          # CRUD de clientes
│   ├── productos/        # CRUD de productos/servicios
│   ├── comprobantes/     # Facturas, boletas, notas
│   ├── notas_credito/     # Notas de crédito
│   ├── sunat_ose/         # Integración SUNAT/OSE
│   ├── reportes/          # Reportes y dashboards
│   └── usuarios/          # Autenticación
├── config/
│   ├── settings/
│   │   ├── base.py        # Configuración base
│   │   ├── local.py       # Desarrollo (SQLite)
│   │   └── production.py  # Producción (PostgreSQL)
│   └── urls.py            # Rutas principales
├── templates/             # Templates HTML
├── docs/                  # Documentación SUNAT
├── docker-compose.yml     # Configuración Docker
├── Dockerfile             # Imagen del backend
├── .env                   # Variables de entorno (NO commitear)
├── .env.example           # Plantilla de variables
├── requirements/
│   ├── base.txt          # Dependencias Python
│   ├── local.txt
│   └── production.txt
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

### Botones en la Interfaz

- **BORRADOR:** "Emitir" (genera XML)
- **EMITIDO:** "Enviar a SUNAT"
- **ENVIADO:** "Consultar Ticket" (auto-consulta)
- **RECHAZADO:** "Reenviar"

---

## 🔌 API REST

### Endpoints Principales

| Método | URL | Descripción |
|--------|-----|-------------|
| POST | `/api/auth/login/` | Iniciar sesión |
| GET | `/api/facturas/` | Listar facturas |
| POST | `/api/facturas/` | Crear factura |
| GET | `/api/comprobantes/{id}/` | Ver comprobante |
| POST | `/api/ose/comprobante/{id}/enviar/` | Enviar a SUNAT |
| POST | `/api/ose/comprobante/{id}/consultar/` | Consultar ticket |
| GET | `/api/reportes/dashboard/` | Dashboard stats |
| GET | `/api/reportes/ventas-por-periodo/` | Reporte de ventas |

### Autenticación

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@prueba.com", "password": "admin"}'

# Respuesta
{
  "token": "abc123...",
  "user": {"id": 1, "email": "admin@prueba.com", ...}
}
```

### Crear Comprobante

```bash
curl -X POST http://localhost:8000/api/facturas/ \
  -H "Authorization: Token TU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "empresa_id": 1,
    "cliente_id": 1,
    "fecha": "2026-04-18",
    "tipo": "01",
    "detalles": [
      {"producto_id": 1, "cantidad": 2, "precio_unitario": 100.00}
    ]
  }'
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

1. Contratar con un OSE certificador (ej: SUNAT, SUMAQ, otros)
2. Obtener credenciales y WSDL
3. Editar `.env`:

```env
SUNAT_OSE_MOCK=False
SUNAT_OSE_WSDL=https://e-beta.sunat.gob.pe/ol-ti-itcpe/billService
SUNAT_OSE_RUC=20512345671
SUNAT_OSE_USUARIO=usuario_ose
SUNAT_OSE_PASSWORD=password_ose
SUNAT_CERT_PATH=/app/media/certificados/certificado.pfx
SUNAT_CERT_PASSWORD=password_cert
```

4. Colocar certificado `.pfx` en `media/certificados/`
5. Reiniciar el servicio

---

## 👤 Credenciales de Acceso

| Rol | Email | Password |
|-----|-------|----------|
| Admin | admin@prueba.com | admin |

---

## 🔧 Resolución de Problemas

### Error: `NoReverseMatch: 'sunat_ose' is not a registered namespace`

```bash
# Asegúrate que el archivo apps/sunat_ose/urls.py tenga:
app_name = 'sunat_ose'
```

### Docker: Puerto 5432 ya en uso

```bash
# Detener PostgreSQL local si está corriendo
docker stop sunat_db
docker rm sunat_db
```

### Cambiar contraseña del admin

```bash
docker-compose exec backend python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
u = User.objects.get(email='admin@prueba.com')
u.set_password('nueva_contrasena')
u.save()
"
```

---

## 📝 Notas de Desarrollo

- El sistema usa IGV del 18% por defecto
- Los comprobantes se numeran automáticamente (F001-00000001, B001-00000001)
- El XML generado cumple con formato UBL 2.1
- Los PDFs se generan con WeasyPrint
- Los logs de envío SUNAT se guardan en `LogEnvioSUNAT`

---

## 📚 Recursos

- [Documentación SUNAT](docs/)
- [Manual técnico OSE v5](docs/Manual%20tecnico%20de%20operatividad%20OSE%20v5/)
- [Guía de integración SUNAT](SUNAT_INTEGRATION_GUIDE.md)

---

**Versión:** 1.0.0  
**Última actualización:** Abril 2026