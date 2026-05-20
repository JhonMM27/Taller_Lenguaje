# Informe: Sistema de Facturacion Electronica - SUNAT

## 1. Estructura del Proyecto

```
apps/
├── sunat_ose/          ← NUCLEO: Integracion con SUNAT/OSE
├── comprobantes/       ← Documentos electronicos (facturas, boletas)
├── empresas/           ← Empresa (RUC) + Certificados digitales
├── clientes/           ← Gestion de clientes
├── productos/          ← Catalogo de productos
├── notas_credito/      ← Notas de credito
├── reportes/           ← Reportes de ventas y dashboard
└── usuarios/           ← Autenticacion de usuarios
```

## 2. Conexiones con SUNAT

### Archivos principales

| Archivo | Funcion | Lineas clave |
|---------|---------|--------------|
| `apps/sunat_ose/ose_client.py` | Cliente SOAP para comunicacion con SUNAT/OSE | L1-336 |
| `apps/sunat_ose/xml_generator.py` | Genera XML UBL 2.1 compatible con SUNAT | L1-453 |
| `apps/sunat_ose/firmar.py` | Firma digital del XML con certificado PKCS#12 | L1-211 |
| `apps/sunat_ose/views.py` | Views para enviar documentos y consultar tickets | L1-312 |
| `apps/sunat_ose/models.py` | Modelo LoteEnvio para envios masivos | L1-32 |
| `wsdl/billService.wsdl` | WSDL SOAP de SUNAT | L39 |

### Endpoints y Credenciales (configurados en `docker-compose.yml:41-49`)

```yaml
WSDL: https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService
RUC OSE: 20103129061
Usuario: MODDATOS
Password: MODDATOS
Certificado: certs/CT2602141470.pfx
Cert Password: Lavagna2026
```

### Operaciones SOAP disponibles (WSDL)

| Operacion | Descripcion | Tipo |
|-----------|-------------|------|
| `sendBill` | Envio individual de comprobante | Sincrono (retorna CDR) |
| `sendPack` | Envio masivo de comprobantes | Asincrono (retorna ticket) |
| `sendSummary` | Envio de resumen diario | Asincrono |
| `getStatus` | Consultar estado de ticket | Sincrono |
| `getStatusAR` | Consultar estado + CDR asincrono | Sincrono |

## 3. Flujo de Envio Individual (sendBill)

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. Usuario hace clic "Enviar a SUNAT"                               │
│    → templates/comprobantes/detalle.html:38                         │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. POST /api/ose/comprobante/<pk>/enviar/                           │
│    → apps/sunat_ose/views.py:23 (EnviarComprobanteView)             │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. Genera XML UBL 2.1                                               │
│    → apps/sunat_ose/xml_generator.py:61 (generar_xml_ubl)           │
│    - Incluye: Proveedor (empresa), Cliente, Impuestos, Lineas       │
│    - Namespaces: cac, cbc, ext, ds, inv                             │
│    - Catalogos SUNAT: listAgencyName='PE:SUNAT'                     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. Firma digital con certificado .pfx (RSA-SHA256)                  │
│    → apps/sunat_ose/firmar.py:87 (firmar_xml)                       │
│    - Carga certificado PFX (sistema de archivos o BD)               │
│    - Crea digest SHA-256 del XML canonico                           │
│    - Firma con RSA-SHA256 usando clave privada                      │
│    - Inserta X509Certificate en ds:KeyInfo                          │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 5. Empaqueta en ZIP                                                 │
│    → apps/sunat_ose/xml_generator.py:444 (crear_zip)                │
│    - Nombre: {RUC}-{TIPO}-{SERIE}-{NUMERO}.zip                      │
│    - Ejemplo: 20103129061-01-F001-00000001.zip                      │
│    - Codifica contenido en Base64                                   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 6. Cliente SOAP (zeep) - real o mock                                │
│    → apps/sunat_ose/ose_client.py:321 (get_ose_client)              │
│    - Si SUNAT_OSE_MOCK=True: MockOSEClient                          │
│    - Si SUNAT_OSE_MOCK=False: OSEClient (SOAP real con zeep)        │
│    - Credenciales formato: {RUC}-{USERNAME}                         │
│    - Autenticacion WSSE UsernameToken                               │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 7. Llamada SOAP: client.service.sendBill(fileName, contentFile)     │
│    → apps/sunat_ose/ose_client.py:105 (send_bill)                   │
│    - Retorna: applicationResponse (CDR en base64)                   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 8. Procesamiento de respuesta                                       │
│    - status=0: ACEPTADO → Guarda CDR, estado='ACEPTADO'             │
│    - status!=0: RECHAZADO → Log error, estado='RECHAZADO'           │
│    → apps/comprobantes/models.py:122 (LogEnvioSUNAT)                │
└─────────────────────────────────────────────────────────────────────┘
```

## 4. Flujo Masivo/Lote (sendPack)

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. Usuario selecciona multiples comprobantes                        │
│    → templates/sunat_ose/envio_masivo.html                          │
│    POST → /api/ose/envio-masivo/enviar/                             │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. View: enviar_lote()                                              │
│    → apps/sunat_ose/views.py:247                                    │
│    - Genera + firma XML de cada comprobante                         │
│    - Empaqueta todos los XML en un solo ZIP                         │
│    - Nombre ZIP: {RUC}-LT-{YYYYMMDD}-1.zip                          │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. SOAP: ose_client.send_pack(zip_base64, file_name)                │
│    → apps/sunat_ose/ose_client.py:195 (send_pack)                   │
│    - Retorna: ticket (asincrono)                                    │
│    - Crea registro LoteEnvio con ticket_ose                         │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. Polling asincrono para consultar estado                          │
│    → apps/sunat_ose/views.py:131 (ConsultarTicketView)              │
│    POST → /api/ose/comprobante/<pk>/consultar/                      │
│    - ose_client.get_status(ticket)                                  │
│    - Si aceptado: ose_client.get_status_cdr(ticket)                 │
│    - Actualiza comprobante.estado = 'ACEPTADO'                      │
└─────────────────────────────────────────────────────────────────────┘
```

## 5. API Endpoints

### Endpoints SUNAT/OSE

| Endpoint | Metodo | View | Funcion |
|----------|--------|------|---------|
| `/api/ose/comprobante/<pk>/enviar/` | POST | `EnviarComprobanteView` | Enviar comprobante individual a SUNAT |
| `/api/ose/comprobante/<pk>/consultar/` | POST | `ConsultarTicketView` | Consultar estado de ticket asincrono |
| `/api/ose/envio-masivo/` | GET | `envio_masivo` | Pagina UI para envio masivo |
| `/api/ose/envio-masivo/enviar/` | POST | `enviar_lote` | Enviar lote de comprobantes |
| `/api/ose/ose/send/` | POST | `mock_send_cdr` | Respuesta CDR mock |
| `/api/ose/ose/consulta/` | POST | `mock_consulta_ticket` | Consulta de ticket mock |

### API REST (Django REST Framework)

| Endpoint | ViewSet | Funcion |
|----------|---------|---------|
| `/api/facturas/` | `ComprobanteViewSet` | CRUD de facturas |
| `/api/boletas/` | `ComprobanteViewSet` | CRUD de boletas |
| `/api/comprobantes/` | `ComprobanteViewSet` | Todos los documentos |
| `/api/clientes/` | `ClienteViewSet` | Gestion de clientes |
| `/api/productos/` | `ProductoViewSet` | Catalogo de productos |
| `/api/notas-credito/` | `NotaCreditoViewSet` | Notas de credito |
| `/api/reportes/ventas-por-periodo/` | `ReporteVentasPeriodoView` | Reportes de ventas |
| `/api/reportes/dashboard/` | `DashboardView` | Metricas del dashboard |

## 6. Tipos de Documentos Soportados

| Codigo | Tipo | Descripcion |
|--------|------|-------------|
| `01` | Factura | Factura estandar (B2B) |
| `03` | Boleta | Boleta de venta (B2C) |
| `07` | Nota de Credito | Nota de credito |
| `08` | Nota de Debito | Nota de debito |

## 7. Implementaciones Especificas de SUNAT

### 7.1 Estructura XML UBL 2.1 (`xml_generator.py`)

- **Elemento raiz:** `<Invoice>` con namespace `urn:oasis:names:specification:ubl:schema:xsd:Invoice-2`
- **Version UBL:** 2.1
- **Customization ID:** 2.0
- **Moneda:** PEN (Sol Peruano)
- **Impuesto:** IGV 18%
- **Catalogos SUNAT:**
  - Tipo documento: `urn:pe:sunat:catalog:01`
  - Exoneracion impuestos: `urn:pe:sunat:catalog:07`

### 7.2 Firma Digital (`firmar.py`)

- **Algoritmo:** RSA-SHA256
- **Formato certificado:** PKCS#12 (.pfx)
- **ID de firma:** `SignatureSUNAT`
- **Canonizacion:** `http://www.w3.org/TR/2001/REC-xml-c14n-20010315`
- **Digest:** SHA-256

### 7.3 Convencion de Nombres ZIP

- **Individual:** `{RUC}-{TIPO}-{SERIE}-{NUMERO}.zip`
- **Lote:** `{RUC}-LT-{YYYYMMDD}-{SECUENCIA}.zip`

## 8. Seguridad

- Las contraseñas de certificados se cifran usando Fernet (cifrado simetrico) derivado de `SECRET_KEY` de Django
- El sistema soporta certificados basados en sistema de archivos y en base de datos
- El modo mock (`SUNAT_OSE_MOCK=True`) permite desarrollo sin credenciales reales de SUNAT
- Los archivos WSDL se almacenan localmente para evitar dependencia de red durante la inicializacion
