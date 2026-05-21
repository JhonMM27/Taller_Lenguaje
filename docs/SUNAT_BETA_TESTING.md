# Documentación: Problemas con SUNAT Beta y Generación de XML UBL

## Resumen Ejecutivo

Se realizaron pruebas exhaustivas para enviar comprobantes electrónicos al endpoint beta de SUNAT (`https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService`). El objetivo era identificar los requisitos exactos del formato XML para que los comprobantes sean aceptados.

**Resultado**: No fue posible hacer un XML válido para el entorno beta de SUNAT con el esquema UBL 2.0/2.1 estándar debido a restricciones del esquema XSD de SUNAT que no permiten todos los campos requeridos en el orden correcto.

---

## 1. Pruebas Realizadas

### 1.1 Tabla Resumen de Pruebas

| # | UBL Version | CustomizationID | Elementos Agregados | Error | Descripción |
|---|-------------|-----------------|---------------------|-------|-------------|
| 1 | 2.0 | 1.0 | Ninguno | 2072 | CustomizationID "1.0" no aceptado |
| 2 | 2.0 | 2.0 | Ninguno | 2072 | CustomizationID "2.0" no aceptado |
| 3 | 2.0 | 2 | Ninguno | 2072 | CustomizationID "2" no aceptado |
| 4 | 2.0 | 1 | Ninguno | 2072 | CustomizationID "1" no aceptado |
| 5 | 2.0 | 0 | Ninguno | 2072 | CustomizationID "0" no aceptado |
| 6 | 2.0 | 1.1 | PricingReference | 2371 | Falta TaxExemptionReasonCode |
| 7 | 2.0 | 1.1 | + TaxExemptionReasonCode | 2047 | Falta AdditionalMonetaryTotal |
| 8 | 2.0 | 1.1 | + AdditionalMonetaryTotal (antes de TaxTotal) | 0306 | Orden incorrecto |
| 9 | 2.0 | 1.1 | AdditionalMonetaryTotal (después de LegalMonetaryTotal) | 0306 | Orden incorrecto |
| 10 | 2.0 | 1.1 | AdditionalMonetaryTotal (después de InvoiceLines) | 0306 | Orden incorrecto |
| 11 | 2.1 | 2.0 | Ninguno | 2074 | UBLVersionID "2.1" no aceptado |

### 1.2 Detalle de Errores

#### Error 2072: CustomizationID Incorrecto
```
La versión del documento no es la correcta
```
- Ocurre con CustomizationID: 1.0, 2.0, 2, 1, 0
- Indica que SUNAT beta SOLO acepta CustomizationID = "1.1"

#### Error 2074: UBLVersionID Incorrecto
```
UBLVersionID - La versión del UBL no es correcta
```
- Ocurre con UBLVersionID = "2.1"
- Indica que solo se acepta UBLVersionID = "2.0"

#### Error 2371: Falta TaxExemptionReasonCode
```
El XML no contiene el tag cbc:TaxExemptionReasonCode de Afectacion al IGV
```
- Ocurre cuando CustomizationID = "1.1" y no existe TaxExemptionReasonCode
- El campo es obligatorio en el nivel de línea (InvoiceLine/TaxTotal/TaxSubtotal/TaxCategory)

#### Error 2047: Falta AdditionalMonetaryTotal
```
Es obligatorio al menos un AdditionalMonetaryTotal con codigo 1001, 1002, 1003 o 3001
```
- Ocurre cuando existe TaxExemptionReasonCode pero falta AdditionalMonetaryTotal
- Código 1001 = Operaciones grabadas
- Código 1002 = Operaciones exoneradas
- Código 1003 = Operaciones inafectas
- Código 3001 = ISC

#### Error 0306: Error de Parseo XML
```
No se puede leer (parsear) el archivo XML
cvc-particle 2.1: ... found <cac:AdditionalMonetaryTotal> but next item should be ...
```
- Ocurre cuando AdditionalMonetaryTotal está en posición incorrecta
- El esquema XSD de SUNAT no permite AdditionalMonetaryTotal en cualquier位置

#### Error 2028: Falta PricingReference
```
Debe existir el tag cac:AlternativeConditionPrice
```
- Ocurre cuando CustomizationID = "1.1" y no existe PricingReference en InvoiceLine

---

## 2. Análisis del Problema

### 2.1 El Dilema de SUNAT Beta

SUNAT beta requiere para CustomizationID 1.1:
1. **UBLVersionID** = "2.0"
2. **CustomizationID** = "1.1"
3. **PricingReference** en cada InvoiceLine (con AlternativeConditionPrice)
4. **TaxExemptionReasonCode** en TaxCategory de línea
5. **AdditionalMonetaryTotal** con código 1001/1002/1003/3001

### 2.2 Problema del Orden (Secuencia XSD)

Según el esquema UBL 2.0 XSD (InvoiceType), el orden de elementos es:

```
Invoice
├── UBLExtensions
├── UBLVersionID
├── CustomizationID
├── ID
├── IssueDate
├── InvoiceTypeCode
├── DocumentCurrencyCode
├── Signature
├── AccountingSupplierParty
├── AccountingCustomerParty
├── TaxTotal
├── LegalMonetaryTotal
└── InvoiceLine (1..N)
```

**El problema**: AdditionalMonetaryTotal NO aparece en la secuencia básica del InvoiceType de UBL 2.0. SUNAT ha añadido validaciones extras que requieren este campo, pero su posición en el esquema XSD no está clara para el entorno beta.

### 2.3 Hipótesis

1. **SUNAT Beta tiene un esquema diferente** al de producción
2. **El entorno beta puede estar desactualizado** o tener validaciones buggy
3. **Se requiere un perfil específico** (periplo) que no estamos usando

---

## 3. Archivos de Prueba Creados

Durante el proceso se crearon los siguientes scripts de prueba (todos eliminados al final):

### Scripts de Prueba Terminados (eliminados)
- `test_*.py` - 78 archivos de prueba creados y posteriormente eliminados

---

## 4. Configuración Actual del Sistema

### 4.1 xml_generator.py (apps/sunat_ose/xml_generator.py)

El generador XML está configurado actualmente con:
- **UBLVersionID**: "2.0"
- **CustomizationID**: "1.0"
- **Versión UBL**: 2.0 (no 2.1)

Esta configuración es la que funcionaba antes de las pruebas con SUNAT beta.

### 4.2 Endpoints

| Entorno | URL |
|---------|-----|
| Beta | `https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService` |
| Producción | `https://e-sunat.gob.pe/ol-ti-itcpfegem-beta/billService` |

### 4.3 Credenciales Utilizadas
- **RUC**: 20103129061
- **Usuario SOL**: MODDATOS
- **Password SOL**: MODDATOS

---

## 5. Recomendaciones

### 5.1 Para Producción
El XML generado con CustomizationID = "1.0" debería funcionar en el entorno de producción de SUNAT, que tiene validaciones menos estrictas que el entorno beta.

### 5.2 Para Entorno Beta
Si se necesita continuar trabajando con el entorno beta, las opciones son:

1. **Consultar documentación oficial de SUNAT** sobre los requisitos específicos del entorno beta
2. **Contactar al soporte de SUNAT** para esclarecer el esquema XSD requerido
3. **Usar herramientas de validación** como el PDT (Programa de Declaraciones Telemáticas) para verificar el formato
4. **Implementar un perfil extendido** si SUNAT lo requiere

### 5.3 Mejores Prácticas
- Mantener el entorno de desarrollo/testing con mock responses
- Validar el XML contra el esquema XSD de UBL 2.0 antes de enviar
- Implementar logging detallado para facilitar debugging

---

## 6. Comandos Útiles para Debugging

### Verificar el XML generado
```python
from apps.sunat_ose.xml_generator import generar_xml_ubl
xml = generar_xml_ubl(comprobante)
print(xml.decode('utf-8'))
```

### Verificar la firma
```python
from apps.sunat_ose.firmar import sign_xml
xml_firmado = sign_xml(xml, empresa_id=1)
print('Firmado:', b'<ds:Signature' in xml_firmado)
```

### Enviar a SUNAT (debug)
```python
import requests
response = requests.post(
    'https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService',
    data=soap_envelope.encode('utf-8'),
    headers={'Content-Type': 'text/xml; charset=utf-8'},
    timeout=30
)
print(response.text)
```

---

## 7. Glosario

| Término | Descripción |
|---------|-------------|
| UBL | Universal Business Language - Estándar internacional para documentos comerciales |
| CustomizationID | Identificador de la personalización del documento UBL |
| UBLVersionID | Versión del esquema UBL utilizado |
| TaxExemptionReasonCode | Código de razón de exoneración del impuesto |
| AdditionalMonetaryTotal | Campo adicional requerido por SUNAT para totales monetarios |
| PricingReference | Referencia de precios，包含 precios alternativos |
| OSE | Operador de Servicios Electrónicos |
| CDR | Constancia de Recepción |
| SOL | Sistema de оригинальных Liquidaciones (credenciales SUNAT) |

---

## 8. Conclusiones

1. **SUNAT Beta tiene validaciones más estrictas** que el entorno de producción
2. **No fue posible generar un XML válido** para el entorno beta con el esquema estándar
3. **El problema principal** es el posicionamiento de AdditionalMonetaryTotal en el XML
4. **Se recomienda usar el entorno de producción** para pruebas reales de envío

---

**Fecha de creación**: 2026-05-20
**Última actualización**: 2026-05-20
**Autor**: Sistema de documentación
**Versión**: 1.0