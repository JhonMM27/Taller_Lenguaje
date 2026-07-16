# Integración SUNAT/OSE

Esta guía explica cómo configurar y usar la integración con SUNAT/OSE en el sistema.

## Modos de operación

El sistema soporta dos modos:

| Modo | Variable | Uso |
|------|----------|-----|
| **Mock** | `SUNAT_OSE_MOCK=True` | Desarrollo y testing. Simula respuestas del OSE. |
| **Real** | `SUNAT_OSE_MOCK=False` | Producción. Conecta con SUNAT Beta o un OSE certificador. |

## Configuración Mock (por defecto)

```env
SUNAT_OSE_MOCK=True
```

El `MockOSEAdapter` (en `infraestructura/sunat/mock_ose.py`) simula:
- `send_bill()`: Devuelve ticket aleatorio + CDR mock.
- `get_status()`: Siempre status=0.
- `get_status_cdr()`: Devuelve CDR mock.

Útil para:
- Desarrollo sin credenciales.
- Tests automatizados.
- Demos.

## Configuración Real (SUNAT Beta)

### 1. Obtener credenciales

Para usar SUNAT Beta necesitas:

1. **RUC** de la empresa emisora (11 dígitos).
2. **Usuario SOL** (`SUNAT_OSE_USUARIO`).
3. **Password SOL** (`SUNAT_OSE_PASSWORD`).
4. **Certificado digital** (.pfx vigente, emitido por una entidad certificadora autorizada).
5. **Contraseña** del certificado.

### 2. Configurar variables

```env
SUNAT_OSE_MOCK=False
SUNAT_OSE_WSDL=https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService
SUNAT_OSE_RUC=20100000001
SUNAT_OSE_USUARIO=JAVISIS1
SUNAT_OSE_PASSWORD=tu_password
SUNAT_CERT_PATH=/app/certs/CT2602141470.pfx
SUNAT_CERT_PASSWORD=tu_cert_password
```

### 3. Cargar el certificado

El certificado se guarda en la BD (tabla `Certificado`) encriptado con Fernet.

```python
python manage.py shell
>>> from apps.empresas.models import Empresa, Certificado
>>> from apps.empresas.services.certificado_service import encrypt_password
>>> empresa = Empresa.objects.first()
>>> with open('/path/cert.pfx', 'rb') as f:
...     pfx_bytes = f.read()
>>> from apps.empresas.services.certificado_service import extraer_metadatos_pfx
>>> meta = extraer_metadatos_pfx(pfx_bytes, 'tu_password')
>>> Certificado.objects.create(
...     empresa=empresa,
...     nombre='Cert Principal',
...     certificado_binario=pfx_bytes,
...     contrasena=encrypt_password('tu_password'),
...     numero_serie=meta['numero_serie'],
...     fecha_desde=meta['fecha_desde'],
...     fecha_hasta=meta['fecha_hasta'],
...     huella_digital=meta['huella'],
...     is_active=True,
... )
```

## Flujo de Emisión

```
┌──────────────┐
│   Cliente    │
│  (Frontend)  │
└──────┬───────┘
       │ POST /api/comprobantes/
       ▼
┌──────────────┐
│  ViewSet DRF │
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│ ComprobanteService   │ (dominio)
│ - Validar tipo doc   │
│ - Numeracion         │
│ - Calcular IGV       │
└──────┬───────────────┘
       │ guardar
       ▼
┌──────────────────────┐
│ DjangoComprobanteRepo│ (infraestructura)
│ - Insertar en BD     │
└──────┬───────────────┘
       │
       ▼
   Comprobante en estado BORRADOR
       │
       │ POST /api/comprobantes/{id}/emitir/
       ▼
   Comprobante en estado EMITIDO (con XML)
       │
       │ POST /api/comprobantes/{id}/enviar/
       ▼
┌──────────────────────┐
│ SunatEnvioService    │ (dominio)
│ - Generar XML UBL    │
│ - Firmar             │
│ - Validar firma      │
│ - Empaquetar ZIP     │
│ - Enviar al OSE      │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ IOSEService (OSE)    │ (infraestructura)
└──────┬───────────────┘
       │
       ▼
   Comprobante en estado ACEPTADO (con CDR)
       │
       │ Si falla
       ▼
   Comprobante en estado RECHAZADO
```

## Estados SUNAT

| Estado | Significado | Acciones posibles |
|--------|-------------|-------------------|
| `BORRADOR` | Recién creado, sin firmar | Emitir, Eliminar |
| `EMITIDO` | XML firmado, listo para enviar | Enviar, Regresar a BORRADOR |
| `ENVIADO` | Enviado al OSE, esperando CDR | Consultar ticket |
| `ACEPTADO` | CDR recibido, válido SUNAT | Anular (vía NC) |
| `RECHAZADO` | OSE rechazó | Reenviar, Anular |
| `ANULADO_PARCIAL` | Anulado parcialmente vía NC | — |
| `ANULADO_TOTAL` | Anulado totalmente vía NC | — |

## Errores Comunes

### `FirmaDigitalInvalida`

El XML no contiene firma digital o falta el certificado X509. Causas:
- El archivo .pfx no se cargo correctamente.
- La contraseña del certificado es incorrecta.
- El certificado está vencido.

### `EnvioSunatFallido`

El OSE rechazó el comprobante. Causas comunes:
- RUC no autorizado para emitir electrónicamente.
- Datos del cliente inválidos.
- Numeración duplicada.
- Certificado expirado.

### `TicketNoEncontrado`

No se ha enviado el comprobante aún, o el ticket fue invalidado por el OSE.

## Tipos de Comprobante

| Código | Tipo | Cliente |
|--------|------|---------|
| `01` | Factura | RUC |
| `03` | Boleta | DNI / CE / Pasaporte |
| `07` | Nota de Crédito | (referencia) |
| `08` | Nota de Débito | (referencia) |

## Cálculo de IGV

```python
subtotal = sum(precio * cantidad) para cada linea
igv = sum(subtotal * 0.18) para cada linea afecto_igv=True
total = subtotal + igv
```

Las líneas con `afecto_igv=False` (exoneradas, inafectas) no suman al IGV.

## Recursos

- [SUNAT - Comprobantes Electrónicos](https://cpe.sunat.gob.pe/)
- [Catálogo de códigos SUNAT](https://cpe.sunat.gob.pe/sites/default/files/inline-images/2019/08/07/catalogo_20190807.pdf)
- [Especificación UBL 2.1](http://docs.oasis-open.org/ubl/UBL-2.1.html)
- [SignXML](https://github.com/XML-Security/signxml)

## Soporte

Para problemas con SUNAT, contacta a tu OSE certificador o al área de soporte de SUNAT.
