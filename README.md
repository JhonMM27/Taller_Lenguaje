# Sistema de Facturacion Electronica SUNAT

Sistema web para emision de comprobantes electronicos (facturas, boletas, notas de credito) que cumple con la normativa SUNAT. Incluye integracion con OSE (Operador de Servicios Electronicos) y modo de simulacion para desarrollo.

## Tecnologias

- **Backend:** Python 3.11, Django 5, Django REST Framework
- **Base de datos:** PostgreSQL 16 (produccion) / SQLite (desarrollo)
- **Documentacion API:** Swagger (drf-spectacular), Redoc
- **Autenticacion:** JWT (SimpleJWT), sesion Django
- **Facturacion electronica:** zeep (SOAP/WSDL), signxml, cryptography
- **PDF:** WeasyPrint
- **Reportes:** pandas, openpyxl
- **Infraestructura:** Docker, Docker Compose, Nginx, Gunicorn

## Modulos

| Modulo        | Descripcion                                                   |
|---------------|---------------------------------------------------------------|
| core          | Modelo base, excepciones, permisos                            |
| empresas      | Gestion de empresas emisoras y certificados digitales         |
| clientes      | CRUD de clientes con validacion de RUC/DNI/CE                 |
| productos     | Productos y categorias con configuracion IGV                  |
| comprobantes  | Emision de facturas (01) y boletas (03)                       |
| notas_credito | Notas de credito electronicas (07)                            |
| sunat_ose     | Integracion SOAP con SUNAT/OSE, generacion XML, firma digital |
| reportes      | Dashboard y reporte de ventas con exportacion Excel           |
| usuarios      | Autenticacion y roles (admin, emisor, contador)               |

## Como ejecutar

### Con Docker (recomendado)

```bash
docker compose up --build
```

Esto levanta backend (puerto 8000), PostgreSQL, Nginx (puertos 80/443) y pgAdmin (puerto 5051).

### Desarrollo local

```bash
# Crear entorno virtual
python -m venv venv

# Activar (Windows)
venv\Scripts\activate

# Activar (Linux/Mac)
source venv/bin/activate

# Instalar dependencias
pip install -r requirements/local.txt

# Copiar y configurar variables de entorno
cp .env.example .env

# Migrar base de datos
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Cargar datos de prueba (opcional)
python manage.py generar_datos_prueba

# Iniciar servidor
python manage.py runserver
```

### Variables de entorno (.env)

```
DEBUG=True
SECRET_KEY=tu-clave-secreta
SUNAT_OSE_MOCK=True   # True = simulacion, False = conexion real
DATABASE_URL=postgres://usuario:password@host:5432/facturacion_db
```

## API

    Endpoints principales:

| Metodo   | Ruta                               | Descripcion                        |
|----------|------------------------------------|------------------------------------|
| POST     | /api/auth/token/                   | Obtener token JWT                  |
| GET/POST | /api/comprobantes/                 | Listar/crear comprobantes          |
| POST     | /api/comprobantes/{id}/emitir/     | Emitir c    omprobante             |
| GET      | /api/comprobantes/{id}/pdf/        | Descargar PDF                      |
| GET      | /api/comprobantes/{id}/xml/        | Descargar XML firmado              |
| GET/POST | /api/clientes/                     | Listar/crear clientes              |
| GET/POST | /api/productos/                    | Listar/crear productos             |
| GET/POST | /api/notas-credito/                | Listar/crear notas de credito      |
| GET      | /api/reportes/dashboard/           | Resumen dashboard                  |
| GET      | /api/reportes/ventas-por-periodo/  | Reporte de ventas                  |

Documentacion interactiva en `/api/docs/swagger/` y `/api/docs/redoc/`.

## Pruebas

```bash
python manage.py test
```

## Licencia

Uso interno.
