# Sistema de Facturación Electrónica SUNAT

Sistema para emitir comprobantes electrónicos (facturas, boletas, notas de crédito) siguiendo normativa SUNAT. Gestiona el ciclo completo: emisión, envío al OSE (mock o real) y respuesta.

## Tabla de Contenidos

- [Características](#características)
- [Stack Tecnológico](#stack-tecnológico)
- [Arquitectura](#arquitectura)
- [Instalación](#instalación)
- [Uso](#uso)
- [API REST](#api-rest)
- [Tests](#tests)
- [Despliegue](#despliegue)
- [Documentación Adicional](#documentación-adicional)

## Características

- **Emisión de comprobantes electrónicos** (facturas, boletas, notas de crédito).
- **Firma digital** de XML UBL 2.1 con certificado .pfx.
- **Envío al OSE/SUNAT** en modo mock (desarrollo) o real (producción).
- **Consulta de tickets** y descarga de CDR (constancia de recepción).
- **Roles y permisos**: ADMIN, EMISOR, CONTADOR.
- **Multi-empresa**: comprobantes filtrados por empresa del usuario.
- **Importación CSV/Excel** masiva de comprobantes.
- **Libro de ventas** simplificado con exportación.
- **Reportes y dashboard** con estadísticas del mes.
- **Soft delete** y auditoría en todos los modelos.
- **Arquitectura Hexagonal** completa (dominio sin Django, inyección de dependencias).

## Stack Tecnológico

| Capa | Tecnología |
|------|------------|
| Backend | Django 6.0 + DRF 3.14 |
| Auth | JWT (SimpleJWT) |
| DB | PostgreSQL 16 / SQLite (dev) |
| Cache | (Opcional) Redis |
| WSGI | Gunicorn |
| Reverse proxy | Nginx |
| Container | Docker + Docker Compose |
| Documentación API | drf-spectacular (Swagger) |
| XML UBL 2.1 | signxml + lxml |
| SOAP SUNAT | zeep |
| PDF | WeasyPrint |
| Excel | pandas + openpyxl |

## Arquitectura

El proyecto sigue una **Arquitectura Hexagonal estricta** con tres capas:

```
.
├── dominio/              ← Python puro, sin Django
│   ├── entidades/        # Dataclasses con lógica de negocio
│   ├── servicios/        # Casos de uso
│   ├── puertos/          # Protocolos (interfaces)
│   ├── excepciones.py    # Jerarquía de errores
│   └── eventos.py        # Eventos del dominio
│
├── infraestructura/      ← Adaptadores Django ORM y externos
│   ├── persistencia/     # Repositorios Django ORM
│   └── sunat/            # Cliente SUNAT/OSE (mock y real)
│
├── interfaces/           ← Adaptadores de entrada
│   ├── api/              # REST (DRF ViewSets)
│   ├── web/              # Templates Django (futuro)
│   └── container.py      # Inyección de dependencias
│
└── apps/                 ← Shell Django (modelos ORM, admin, urls)
```

### Reglas de Dependencias

- `dominio/` NO importa Django, settings, ni modelos ORM.
- `infraestructura/` implementa los puertos del dominio usando Django/SOAP.
- `interfaces/` llama al dominio vía `container` (DI).
- `apps/` mantiene modelos ORM y admin (es la "concha" de Django).

Para más detalles ver [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md).

## Instalación

### Opción 1: Local con venv

```bash
# Clonar
git clone <repo>
cd Proyecto_Final

# Crear venv
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Instalar
pip install -r requirements/local.txt

# Configurar .env
cp .env.example .env
# Editar .env con tus valores

# Migrar
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Cargar datos iniciales (opcional)
python manage.py loaddata fixtures/initial_data.json  # si existe

# Levantar
python manage.py runserver
```

### Opción 2: Docker Compose

```bash
# Levantar todo (Django + Postgres + pgAdmin + Nginx)
docker compose up --build

# Aplicar migraciones
docker compose exec backend python manage.py migrate

# Crear superusuario
docker compose exec backend python manage.py createsuperuser

# Cargar certificados
docker compose exec backend python manage.py shell
>>> from apps.empresas.models import Empresa
>>> Empresa.objects.create(ruc='20100000001', razon_social='Mi Empresa')
```

Acceder a:
- Web: http://localhost
- Admin: http://localhost/admin/
- API: http://localhost/api/
- Swagger: http://localhost/api/docs/swagger/
- Health: http://localhost/api/health/
- pgAdmin: http://localhost:5051 (admin@sunat.local.com / admin123)

## Uso

### Como Emisor

1. Login en http://localhost (usuario con rol EMISOR).
2. Ir a **Dashboard** para ver estadísticas.
3. Ir a **Clientes** → registrar RUC/DNI del cliente.
4. Ir a **Productos** → registrar productos con código y precio.
5. Ir a **Emitir Comprobante**:
   - Seleccionar tipo (Factura/Boleta).
   - Buscar cliente por RUC/DNI.
   - Agregar líneas de productos.
   - El cálculo de IGV se hace en tiempo real.
6. Click en **Emitir** → cambia a estado EMITIDO.
7. Click en **Enviar a SUNAT** → procesa y devuelve CDR.

### Como Contador

1. Login con rol CONTADOR.
2. Ir a **Reportes** → **Libro de Ventas** para ver libro mensual.
3. Descargar en CSV/Excel.

### Como Admin

1. Acceso completo a todas las vistas.
2. Gestionar empresas, certificados, usuarios y roles.

## API REST

Documentación completa en Swagger: http://localhost/api/docs/swagger/

### Endpoints principales

| Método | URL | Descripción |
|--------|-----|-------------|
| POST | `/api/auth/token/` | Obtener JWT |
| POST | `/api/comprobantes/` | Crear comprobante (factura/boleta) |
| GET | `/api/comprobantes/` | Listar comprobantes con filtros |
| POST | `/api/comprobantes/{id}/emitir/` | Cambiar BORRADOR → EMITIDO |
| POST | `/api/comprobantes/{id}/reenviar/` | Reenviar RECHAZADO |
| GET | `/api/comprobantes/{id}/pdf/` | Descargar PDF |
| GET | `/api/comprobantes/{id}/xml/` | Descargar XML firmado |
| POST | `/api/comprobantes/{id}/enviar/` | Enviar a SUNAT/OSE |
| DELETE | `/api/comprobantes/{id}/eliminar_soft/` | Soft delete |
| POST | `/api/notas-credito/` | Crear NC contra comprobante |
| POST | `/api/notas-credito/{id}/enviar/` | Enviar NC |
| GET | `/api/clientes/` | CRUD clientes |
| GET | `/api/productos/` | CRUD productos |
| GET | `/api/reportes/ventas-por-periodo/?mes=&anio=` | Libro de ventas |

### Autenticación

```bash
# Obtener token
curl -X POST http://localhost/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin", "password":"admin123"}'

# Usar token
curl http://localhost/api/comprobantes/ \
  -H "Authorization: Bearer <access_token>"
```

### Ejemplo: Crear factura

```bash
curl -X POST http://localhost/api/comprobantes/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "empresa_id": 1,
    "cliente_id": 1,
    "fecha": "2026-07-15",
    "tipo": "01",
    "detalles": [
      {"producto_id": 1, "cantidad": "2"}
    ]
  }'
```

## Tests

```bash
# Activar venv
.venv\Scripts\activate

# Todos los tests
pytest

# Solo dominio (sin BD)
pytest dominio/tests/ -p no:django

# Solo infraestructura
pytest infraestructura/tests/

# Solo interfaces
pytest interfaces/tests/

# Con cobertura
pytest --cov=dominio --cov=infraestructura --cov=interfaces --cov=apps --cov-report=term-missing

# Reporte HTML
pytest --cov --cov-report=html
# Ver htmlcov/index.html
```

### Cobertura

| Capa | Cobertura objetivo |
|------|-------------------|
| Dominio (entidades) | ≥ 85% |
| Dominio (servicios) | ≥ 60% |
| Infraestructura | ≥ 70% |
| Interfaces (API) | ≥ 60% |
| **TOTAL** | **≥ 60%** |

## Despliegue

### Producción con Docker

```bash
# Configurar .env.production con valores reales
# SUNAT_OSE_MOCK=False
# SUNAT_OSE_WSDL=https://...
# SUNAT_OSE_RUC, USUARIO, PASSWORD
# SUNAT_CERT_PATH=/app/certs/cert.pfx
# SUNAT_CERT_PASSWORD=...

# Build
docker compose -f docker-compose.yml -f docker-compose.prod.yml build

# Push
docker push <registry>/<image>
```

### Checklist producción

- [ ] `DEBUG=False`
- [ ] `SECRET_KEY` único en variable de entorno
- [ ] `ALLOWED_HOSTS` configurado
- [ ] `SUNAT_OSE_MOCK=False`
- [ ] Certificado .pfx cargado y vigente
- [ ] Contraseña del certificado en variable de entorno
- [ ] PostgreSQL con backups
- [ ] Nginx con HTTPS
- [ ] `collectstatic` ejecutado
- [ ] Logs centralizados

## Documentación Adicional

- [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md) - Detalle de la arquitectura hexagonal.
- [docs/SUNAT.md](docs/SUNAT.md) - Manual de integración con SUNAT.
- [docs/MIGRACIONES.md](docs/MIGRACIONES.md) - Cómo migrar desde versiones anteriores.
- [docs/TESTING.md](docs/TESTING.md) - Estrategia y ejecución de tests.

## Estructura del Proyecto

```
.
├── apps/                          # Apps Django (shell)
│   ├── comprobantes/              # Modelos de comprobantes
│   ├── notas_credito/             # Modelos de NC
│   ├── clientes/                  # Modelos de clientes
│   ├── productos/                 # Modelos de productos
│   ├── empresas/                  # Modelos de empresas y certificados
│   ├── sunat_ose/                 # Servicios legacy SUNAT
│   ├── reportes/                  # Reportes y dashboard
│   ├── usuarios/                  # Usuarios y perfiles
│   └── core/                      # ModeloBase, permisos, excepciones
│
├── dominio/                       # ★ Arquitectura hexagonal ★
├── infraestructura/               # Adaptadores
├── interfaces/                    # API + web
│
├── config/                        # Settings Django
├── templates/                     # Templates HTML
├── static/                        # Archivos estáticos
├── requirements/                  # Dependencias
│
├── docker-compose.yml
├── Dockerfile
├── manage.py
├── pytest.ini
├── .coveragerc
└── README.md
```

## Licencia

MIT

## Contacto

Taller de Lenguaje de Programación - Proyecto Final
SUNAT-ready
