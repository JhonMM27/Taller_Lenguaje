# Integración SUNAT/OSE

Esta guía explica cómo configurar y usar la integración con SUNAT/OSE en el sistema.

## Guías funcionales

- [Exportación de bienes con SUNAT-40](EXPORTACION_SUNAT_40.md)

## Afectaciones gratuitas

- En códigos `11-16`, `21` y `31-37`, el precio es referencial y no incrementa el total pagable.
- La base referencial se informa en `LineExtensionAmount` y `TaxableAmount` para evitar los errores SUNAT `3271` y `3272`.
- Los códigos `11-16` informan IGV referencial dentro del subtotal `9996`, pero no lo suman al impuesto cobrado.
- El XML agrega automáticamente la leyenda `1002`.

## Modos de operación

El sistema soporta dos modos:

| Modo | Variable | Uso |
|------|----------|-----|
| **Mock** | `SUNAT_OSE_MOCK=True` | Desarrollo y testing. Simula respuestas del OSE. |
| **Real** | `SUNAT_OSE_MOCK=False` | Producción. Conecta con SUNAT Beta o un OSE certificador. |

## Configuración Mock

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
   RECHAZADO (CDR tributario) o ERROR_ENVIO (fallo técnico)
```

## Estados SUNAT

> Regla vigente: `RECHAZADO` significa rechazo tributario definitivo para esa
> numeracion y requiere crear un comprobante nuevo. `ERROR_ENVIO` identifica un
> fallo tecnico sin CDR de rechazo y es el unico estado que permite reintentar.
> Los comprobantes `BORRADOR` pueden editarse; los `ACEPTADO` se corrigen con NC/ND.

| Estado | Significado | Acciones posibles |
|--------|-------------|-------------------|
| `BORRADOR` | Recién creado, sin firmar | Emitir, Eliminar |
| `EMITIDO` | XML firmado, listo para enviar | Enviar, Regresar a BORRADOR |
| `ENVIADO` | Enviado al OSE, esperando CDR | Consultar ticket |
| `ACEPTADO` | CDR recibido, válido SUNAT | Anular (vía NC) |
| `RECHAZADO` | SUNAT/OSE rechazó con CDR; la numeración quedó utilizada | Corregir y generar un comprobante nuevo |
| `ERROR_ENVIO` | Fallo técnico sin CDR de rechazo | Reintentar con la misma numeración |
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
| `01` | Factura nacional | RUC |
| `01` + operación `0200` | Factura de exportación | Receptor no domiciliado, documento extranjero de 1-15 caracteres y país distinto de `PE` |
| `03` | Boleta | DNI / CE / Pasaporte |
| `07` | Nota de Crédito | (referencia) |
| `08` | Nota de Débito | (referencia) |

> Los 11 dígitos corresponden exclusivamente al tipo `6 - RUC peruano`.
> Para exportación, los tipos `0`, `4`, `7` y `A` aceptan documentos de 1 a 15
> caracteres sin espacios; no deben rellenarse con ceros para llegar a 11.

## Cálculo de IGV

| Afectación | Base comercial | Impuesto | Total pagable |
|---|---:|---:|---:|
| `10` Gravada | Precio neto | 18% IGV | Base + IGV |
| `17` IVAP | Precio neto | 4% IVAP | Base + IVAP |
| `20`, `30`, `40` | Precio neto | 0 | Base |
| `11-16`, `21`, `31-37` | 0; se conserva base referencial XML | IGV solo referencial para `11-16` | 0 |

## Recursos

- [SUNAT - Comprobantes Electrónicos](https://cpe.sunat.gob.pe/)
- [SUNAT - Guías, anexos y reglas de validación vigentes](https://cpe.sunat.gob.pe/guias-y-manuales)
- [SUNAT - Guía XML de factura UBL 2.1](https://cpe.sunat.gob.pe/sites/default/files/inline-files/guia%2Bxml%2Bfactura%2Bversion%202-1%2B1%2B0%20%282%29_0%20%282%29.pdf)
- [OASIS - Especificación UBL 2.1](https://docs.oasis-open.org/ubl/UBL-2.1.html)
- [SignXML](https://github.com/XML-Security/signxml)

## Soporte

Para problemas con SUNAT, contacta a tu OSE certificador o al área de soporte de SUNAT.
