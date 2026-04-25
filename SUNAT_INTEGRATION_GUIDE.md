# CONFIGURACIÓN SUNAT - BETA / DESARROLLO

## Resumen del Sistema Actual

El sistema actualmente tiene un **Mock OSE** que simula respuestas de SUNAT. 
Para pasar a beta/desarrollo con SUNAT real, debes modificar los siguientes archivos:

---

## 📁 ARCHIVOS A MODIFICAR

### 1. `apps/sunat_ose/xml_generator.py` - Generación XML UBL 2.1
```
Ubicación: apps/sunat_ose/xml_generator.py
Función: Genera el XML en formato UBL 2.1 según规范 SUNAT
Estado: ✅ Implementado (mock signing)
Para producción: Requiere firma digital real con certificado
```

### 2. `apps/sunat_ose/views.py` - Envío a OSE/SUNAT
```
Ubicación: apps/sunat_ose/views.py
Función: Recibe comprobantes y los envía al OSE
Estado: ✅ Implementado (mock respuestas)
Para beta: Cambiar endpoints a OSE real (SUNAT o SUMAQ)
```

### 3. `apps/sunat_ose/mock_ose.py` - Mock OSE (REEMPLAZAR)
```
Ubicación: apps/sunat_ose/mock_ose.py
Función: Simula respuestas del OSE
Estado: ⚠️ USAR SOLO EN DESARROLLO
Para beta: Reemplazar con cliente SOAP real
```

---

## 🔧 CONFIGURACIÓN PARA BETA

### Opción A: OSE de Prueba (SUNAT proporciona entorno de pruebas)

Endpoints de prueba SUNAT:
```
OSE Beta: https://e-beta.sunat.gob.pe/ol-ti-itcpe/billService
o el que te proporcione tu OSE certificado
```

### Opción B: Usar un OSE certificador (ej: SUMAQ, others)

```
SUMAQ (ejemplo): https://ose.sumaq.pe/billService
Verificar con tu OSE los endpoints y credenciales
```

---

## 📋 PASOS PARA ACTIVAR BETA

### Paso 1: Configurar credentials OSE

Crear archivo `config/.env` (no commitear):
```
SUNAT_OSE_URL=https://e-beta.sunat.gob.pe/ol-ti-itcpe/billService
SUNAT_OSE_RUC=TuRUCEmisor
SUNAT_OSE_USUARIO=usuario_beta
SUNAT_OSE_PASSWORD=password_beta
SUNAT_CERT_PATH=/path/to/certificado.pfx
SUNAT_CERT_PASSWORD=password_certificado
```

### Paso 2: Reemplazar mock_ose.py con cliente SOAP real

```python
# apps/sunat_ose/ose_client.py (NUEVO)
import zeep
from lxml import etree

class SunatOSEClient:
    def __init__(self, wsdl_url, ruc, usuario, password):
        self.client = zeep.Client(wsdl_url)
        self.ruc = ruc
        self.usuario = usuario
        self.password = password
    
    def send_bill(self, xml_firmado, nombre_archivo):
        response = self.client.service.sendBill(
            zipContent=xml_firmado,
            fileName=nombre_archivo
        )
        return response
    
    def get_status(self, ticket):
        return self.client.service.getStatus(ticket)
```

### Paso 3: Modificar views.py para usar cliente real

```python
# En apps/sunat_ose/views.py - reemplazar POST logic

from apps.sunat_ose.ose_client import SunatOSEClient

def enviar_a_ose(comprobante):
    client = SunatOSEClient(
        wsdl_url=settings.SUNAT_OSE_WSDL,
        ruc=settings.SUNAT_OSE_RUC,
        usuario=settings.SUNAT_OSE_USUARIO,
        password=settings.SUNAT_OSE_PASSWORD
    )
    
    xml_content = generar_xml_ubl(comprobante)
    xml_firmado = firmar_xml(xml_content, settings.SUNAT_CERT_PATH)
    zip_content = crear_zip(xml_firmado, comprobante.nombre_zip)
    
    response = client.send_bill(zip_content, comprobante.nombre_zip + '.zip')
    return response
```

---

## 🔒 CERTIFICADO DIGITAL

Para firma digital real, necesitas:

1. **Obtener certificado digital** de una CA autorizada (SUNAT认可)
2. **Formato**: .pfx o .p12
3. **Colocar** en una ruta accesible (configurable via env)
4. **Usar** librerías como `signxml` o `xmlsec` para firmar

```python
# Ejemplo firma con signxml
from signxml import XMLSigner
from pathlib import Path

def firmar_xml_real(xml_content, cert_path, cert_password):
    cert = Path(cert_path).read_bytes()
    signer = XMLSigner()
    return signer.sign(xml_content, key=cert, passphrase=cert_password)
```

---

## 📊 MODELO DE DATOS PARA SUNAT

### Campos requeridos en Empresa:
- `ruc` - 11 dígitos
- `razon_social` - Nombre legal
- `direccion` - Dirección fiscal
- `ubigeo` - Código ubigeo (6 dígitos)
- `regimen_tributario` - GENERAL, RER, MYPE, etc.

### Campos requeridos en Comprobante:
- `tipo` - 01=Factura, 03=Boleta, 07=NC, 08=ND
- `serie` - F001, B001, etc.
- `numero` - Correlativo 8 dígitos
- `fecha` - Formato YYYY-MM-DD
- `cliente` - Con tipo_doc y num_doc válidos

---

## 🚀 FLUJO DE ENVÍO

```
1. Crear comprobante (BORRADOR)
2. Emitir (EMITIDO) - Genera XML
3. Enviar a OSE (ENVIADO) - SOAP call
4. OSE retorna ticket (async)
5. Consultar ticket (getStatus)
6. OSE retorna CDR (ACEPTADO/RECHAZADO)
```

---

## 📝 NOTAS IMPORTANTES

1. **Mock OSE** (`mock_ose.py`) solo simula - NO conecta a SUNAT real
2. Para beta necesitas contrato con OSE certificador
3. Cada OSE tiene sus propios endpoints y credenciales
4. El entorno de pruebas de SUNAT tiene límites de volumen

---

## 🔗 RECURSOS

Documentación SUNAT OSE:
- `docs/Manual tecnico de operatividad OSE v5/`
- `docs/guia+xml+factura+version 2-1+1+0 (2)_0 (2)/`
- `docs/validaciones/` - XSD para validación

Hojas de cálculo validaciones:
- `docs/AjustesValidacionesCPEv20260212.xlsx`
- `docs/Validaciones_Servicios_Publicos_06022020_publicacion.xlsx`