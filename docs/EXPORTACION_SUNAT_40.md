# Exportación de bienes con SUNAT-40

`SUNAT-40` es el producto de ejemplo configurado con el código de afectación IGV
`40 - Exportación`. No es un impuesto adicional ni una transferencia gratuita.
Representa una venta de bienes hacia un receptor no domiciliado, sin IGV.

## Comportamiento automático

Cuando todas las líneas del comprobante tienen afectación `40`, el sistema:

- genera una factura electrónica tipo `01`, con serie `F...`;
- deriva automáticamente el tipo de operación SUNAT `0200`;
- usa el tributo `9995 / EXP / FRE` con tasa `0.00`;
- conserva el valor de venta y el total pagable;
- usa la moneda elegida: `PEN`, `USD` o `EUR`;
- identifica al receptor como no domiciliado y envía su país ISO-3166.

El usuario no escribe `0200` manualmente. El servicio lo determina a partir de
las líneas con afectación `40` y lo valida nuevamente antes de generar el XML.

## 1. Registrar al cliente extranjero

En **Clientes → Nuevo cliente** complete:

| Campo | Valor requerido |
|---|---|
| Tipo de documento | `0`, `4`, `7` o `A` |
| Número | Documento extranjero de **1 a 15 caracteres**, sin espacios; su longitud depende del país emisor |
| Razón social | Nombre o denominación del comprador extranjero |
| País ISO | Código ISO-3166 de dos letras distinto de `PE`, por ejemplo `US`, `CL` o `ES` |

El tipo `0` significa **Documento tributario no domiciliado sin RUC**. Una
exportación no puede usar un receptor con RUC peruano ni un país `PE`.

Los **11 dígitos solo se exigen cuando se selecciona el tipo `6 - RUC
peruano`**. El documento extranjero no se completa ni se rellena con ceros para
llegar a 11 posiciones. Debe registrarse tal como fue emitido en su país,
siempre que tenga entre 1 y 15 caracteres y no contenga espacios.

Ejemplo:

```text
Tipo de documento: 0
Número: ABC123
Razón social: FOREIGN BUYER LLC
País ISO: US
```

Otros ejemplos de longitudes aceptadas por el sistema son `987654321` (9
caracteres) y `FOREIGN-001` (11 caracteres). La longitud no determina si el
receptor es extranjero: lo determinan el **tipo de documento extranjero** y el
**país distinto de PE**.

### Si el formulario exige 11 dígitos

Revise el campo **Tipo de documento**. Si está seleccionado `6 - RUC peruano`,
el navegador exigirá correctamente 11 dígitos. Para un comprador no
domiciliado sin RUC peruano seleccione `0 - Documento tributario extranjero`, o
el tipo real que corresponda (`4`, `7` o `A`). El formulario cambiará la regla
a 1-15 caracteres automáticamente.

## 2. Crear la factura de exportación

1. Abra **Comprobantes → Nuevo comprobante**.
2. Seleccione la empresa emisora.
3. Seleccione el cliente extranjero.
4. Elija **Factura**.
5. Seleccione la moneda de la operación.
6. Agregue `SUNAT-40 - Bien destinado a exportación`.
7. Ingrese cantidad y precio de venta.
8. Guarde, revise, emita y envíe normalmente.

Una factura de exportación solo puede contener productos con afectación `40`.
Para varios productos exportados, todos deben estar configurados con ese código.

## Restricciones

El sistema bloquea antes del envío:

- una boleta con afectación `40`;
- una factura `0200` dirigida a un cliente con RUC;
- un cliente extranjero con país `PE`;
- la mezcla de líneas `40` con gravadas, exoneradas, inafectas o gratuitas;
- un `tipo_operacion` que no coincida con la afectación de las líneas.

El soporte actual cubre **exportación de bienes `0200`**. No implementa todavía
las variantes SUNAT `0201` a `0208` para otros tipos especiales de exportación.

## XML esperado

Para una venta de USD 100.00, los nodos principales son:

```xml
<cbc:ProfileID>0200</cbc:ProfileID>
<cbc:InvoiceTypeCode listID="0200">01</cbc:InvoiceTypeCode>
<cbc:DocumentCurrencyCode>USD</cbc:DocumentCurrencyCode>

<cbc:ID schemeID="0">ABC123</cbc:ID>

<cbc:TaxableAmount currencyID="USD">100.00</cbc:TaxableAmount>
<cbc:TaxAmount currencyID="USD">0.00</cbc:TaxAmount>
<cac:TaxScheme>
  <cbc:ID>9995</cbc:ID>
  <cbc:Name>EXP</cbc:Name>
  <cbc:TaxTypeCode>FRE</cbc:TaxTypeCode>
</cac:TaxScheme>
<cbc:TaxExemptionReasonCode>40</cbc:TaxExemptionReasonCode>
```

## Notas de crédito y rechazos

- Una nota de crédito de exportación hereda moneda, receptor y operación `0200`
  de la factura original.
- Una factura rechazada por SUNAT no se reenvía con la misma numeración.
- Use **Corregir y generar nuevo comprobante** para conservar el rechazo y crear
  una nueva factura con otro correlativo.
- `ERROR_ENVIO` sí permite reintentar porque representa un fallo técnico sin CDR
  de rechazo.

## Productos de prueba

Para crear o actualizar los 19 ejemplos del Catálogo 07:

```powershell
docker compose exec -T backend python manage.py crear_productos_sunat_ejemplo
```

El comando es idempotente: puede ejecutarse nuevamente sin duplicar productos.

## Referencias oficiales

- [SUNAT - Tipos de comprobantes de pago](https://cpe.sunat.gob.pe/informacion_general/tipos_comprobantes_pago): confirma que la factura normalmente se emite a un adquirente con RUC y exceptúa a los sujetos no domiciliados en operaciones de exportación.
- [SUNAT - Guía XML de factura UBL 2.1](https://cpe.sunat.gob.pe/sites/default/files/inline-files/guia%2Bxml%2Bfactura%2Bversion%202-1%2B1%2B0%20%282%29_0%20%282%29.pdf): define `CompanyID`, `schemeID` y los tipos del Catálogo 06, incluido el código `0` para el no domiciliado sin RUC.
- [SUNAT - Guías y reglas de validación vigentes](https://cpe.sunat.gob.pe/guias-y-manuales): fuente que debe revisarse antes de cambiar reglas XML o catálogos.
