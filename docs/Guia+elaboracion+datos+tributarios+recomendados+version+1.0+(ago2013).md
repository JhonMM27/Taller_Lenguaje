Datos tributarios recomendados V 1.0 ~ 1 ~

## Contenido

**GUIA DE ELABORACION DE**

**DOCUMENTOS ELECTRONICOS XML**

**Datos Tributarios**

**Recomendados**

**Versión 1.**

#### SUPERINTENDENCIA NACIONAL DE ADUANAS Y ADMINISTRACIÓN TRIBUTARIA

#### SUNAT - Lima – Perú

#### Agosto 2013

## Emisión electrónica desde los

## Sistemas del Contribuyente

#### RS 097-2012/SUNAT

#### RS 065-2013/SUNAT

## INDICE

- Normas de Uso de los datos tributarios recomendados
- 1 DETRACCIONES
  - 1.1 Forma de consignar la información
  - 1.2 Ejemplo de una factura con un concepto de detracción
- 2 SERVICIOS DE HOSPEDAJE
  - 2.1 Forma de consignar la información.
  - 2.2 Servicio de hospedaje.
  - 2.3 Servicio de alimentación.-
    - A. En caso este servicio sea prestado directamente al sujeto no domiciliado....
      - paquete turístico B. En caso este servicio sea prestado a un sujeto no domiciliado que opte por un
  - 2.4 Ejemplo - Servicio hospedaje Paquete Turístico

### INTRODUCCION

### Normas de Uso de los datos tributarios recomendados

Con la publicación de la Resolución de Superintendencia 097-2012/SUNAT y modificatorias, se

regula la emisión electrónica de los comprobantes de pago en el Perú, adoptándose el formato

XML (Extensible Markup Language) basado en el estándar UBL (Universal Business Language)

2.0 referido en la página web [http://www.oasis-open.org,](http://www.oasis-open.org,) como el soporte digital del documento

electrónico.

En tal sentido, la SUNAT ha publicado documentos de trabajo denominados Guías de

#### elaboración de los documentos electrónicos XML, que tienen por objetivo describir las normas

de uso para la construcción de la factura, boleta de venta, notas de crédito y debito

electrónicas, así como de la Comunicación de Baja y del Resumen Diario, cuyo contenido o

información tributaria se encuentra regulada por la referida Resolución de Superintendencia,

información que a su vez se enmarca en el Reglamento de Comprobantes de Pago (R.S. N°

007 - 99/SUNAT), norma rectora de todos los documentos que acreditan las transferencia de

bienes o prestación de servicios en el país.

Sin embargo, el sistema tributario peruano contiene particularidades que afectan directa o

indirectamente la emisión y contenido de un comprobante de pago, toda vez que el uso del

papel como soporte de dicho documento ha permitido, al emisor, consignar información

adicional a la requerida por las regulaciones pertinentes, pero necesaria para lograr una

oportuna y correcta gestión tributaria

Es así, que la interacción con distintas empresas durante la etapa piloto de la implementación

de comprobante de pago electrónico, ha permitido identificar cierta información, que

corresponde con la comentada en el párrafo anterior, es decir aquella que no siendo requisito

exigido propiamente por las normas tributarias, sí necesitan ser identificadas dentro del

estándar UBL a fin de facilitar la gestión del proceso de facturación del emisor electrónico.

En tal sentido, en el presente documento se presentan las recomendaciones de uso necesarias

para representar información que siendo de naturaleza tributaria, no se encuentra contenida

en la RS 097-2012/SUNAT y modificatorias.

En esta primera versión, se aborda información relacionada con el Régimen de Detracciones y

Servicio de Hospedajes.

Cabe señalar que el presente documento será actualizado en la medida que se evalúen

nuevos requerimientos por parte de los emisores electrónicos o nuevas regulaciones que

impacten en la emisión electrónica que ameriten la intervención de la Administración Tributaria.

## 1 DETRACCIONES

#### Con la finalidad de facilitar al emisor electrónico, el control administrativo de las

#### diferentes operaciones de este concepto tributario, se identificaron un conjunto de

#### datos o información que se detalla en el cuadro 1, que requieren ser incluidos en la

#### factura electrónica.

#### Por tal motivo, en este rubro se definen los elementos (tag ́s) a utilizar para la

#### identificación y/o construcción de datos relacionados con el Régimen de

#### Detracciones, descritos en el cuadro 1.

#### Cabe señalar que el uso de los referidos elementos es opcional, y que se han

#### definido a fin de estandarizar y facilitar su incorporación en el documento

#### electrónico, considerando la normatividad vigente.

CUADRO 1

```
Campo
Definición
Nivel
```

```
Condición
Informática
```

```
Tipo y
longitud
```

```
Formato
```

% DETRACCION 1 Porcentaje de detracción Global^ C^ n..2^ n(2)^

MONTO 2 Monto de la detracción Global^ C^ an...15^ n(12,2)^

CODIGO DE BB Y SS
SUJETOS A
DETRACCION

```
3 Código de bienes y servicios
sujetos al sistema. De acuerdo
al anexo 4 de la RS 183-
2004/SUNAT
```

```
Global C n..3 n(3)
```

##### NUMERO DE CTA EN

##### EL BN

```
3 Número de cuenta del proveedor
en el BN
```

```
Global C n11 n(11)
```

##### VALOR

##### REFERENCIAL

```
Usado en el caso de
detracción al transporte de
bienes por vía terrestre
5 Valor referencial del servicio de
transporte de bienes realizado
por vía terrestre, determinado de
conformidad con lo dispuesto en
el DS N°010- 2006 - MTC, que
aprobó la Tabla de Valores
Referenciales para la aplicación
del Sistema al servicio de
transporte de bienes realizado
por vía terrestre.
```

```
Global C an...15 n(12,2)
```

##### RECURSOS

##### HIDROBIOLOGICOS

```
En el caso de la venta de
recursos hidrobiológicos,
sujetos a detracción:
6 a. Nombre y matrícula de la
embarcación pesquera utilizada
para efectuar la extracción y
descarga de los bienes
vendidos, en los casos que se
hubiera utilizado dicho medio
```

```
Global C an...
```

```
7 b. descripción del tipo y cantidad
de la especie vendida
```

```
Global C an...
```

```
8
c. Lugar de la descarga
```

```
Global C an..
```

##### 9

```
d. Fecha en que se realiza la
descarga
```

```
Global C an..10 yyyy-mm-dd
```

### 1.1 Forma de consignar la información

```
Para consignar la información, se requiere utilizar los conceptos y elementos codificados
```

```
en los anexos 14 y 15 respectivamente, de la Resolución de Superintendencia 097-
```

```
2012/SUNAT y modificatorias.
```

```
Los siguientes datos, se ubicarán en el tag <sac:AdditionalMonetaryTotal>,
```

```
a) Porcentaje de la detracción
```

```
b) Monto de la detracción
```

```
c) Valor referencial, en el caso de detracciones al transporte de bienes por vía
```

```
terrestre
```

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sac:AdditionalInformation/sac:Additional
MonetaryTotal/cbc:ID (Código del tipo de elemento - Catálogo No. 14)
/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sac:AdditionalInformation/sac:Additional
MonetaryTotal/sac:ReferenceAmount (Valor referencial )
/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sac:AdditionalInformation/sac:Additional
MonetaryTotal/cbc:PayableAmount (Monto de la detracción)
/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sac:AdditionalInformation/sac:Additional
MonetaryTotal/cbc:Percent (Porcentaje de la detracción)
```

```
Los siguientes datos, se ubicarán en el tag <sac:AdditionalProperty>,
```

```
a) Código de bienes y servicios sujetos a detracción
```

```
b) Número de Cuenta en el Banco de la Nación
```

```
c) Recursos Hidrobiológicos-Nombre y matrícula de la embarcación
```

```
d) Recursos Hidrobiológicos-Tipo y cantidad de especie vendida
```

```
e) Recursos Hidrobiológicos-Lugar y fecha de descarga
```

```
f) Recursos Hidrobiológicos-Fecha de descarga
```

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sac:AdditionalInformation/sac:Additional
Property/cbc:ID (Código del concepto - Catálogo No. 15)
/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sac:AdditionalInformation/sac:Additional
Property/cbc:Value (Valor del concepto)
```

```
Guía de elaboración de documentos electrónicos XML - UBL 2.
```

```
Datos tributarios recomendados V 1.0 ~ 7 ~
```

```
N° DATO NIVEL CONDICIÓN
INFORMÁTICA
(1)
```

```
TIPO Y
LONGITUD
(2)
```

```
FORMATO TAG UBL
```

```
1 Porcentaje de detracción^ Global^ C^
```

```
an4 /Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sac:AdditionalInformation/sac:Ad
ditionalMonetaryTotal/cbc:ID (Código del tipo de elemento - Catálogo No. 14)
an...18 n(15,2) /Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sac:AdditionalInformation/sac:Ad
ditionalMonetaryTotal/cbc:Percent (Porcentaje de la detracción)
```

##### 2

```
Monto de la detracción Global C
```

```
an4 /Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sac:AdditionalInformation/sac:Ad
ditionalMonetaryTotal/cbc:ID (Código del tipo de elemento - Catálogo No. 14)
an...18 n(15,2) /Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sac:AdditionalInformation/sac:Ad
ditionalMonetaryTotal/cbc:PayableAmount (Monto de la detracción)
```

##### 3

```
Código de bienes y servicios sujetos al
sistema. De acuerdo al anexo 4 de la
RS 183-2004/SUNAT
```

```
Global C
```

```
an4 /Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sac:AdditionalInformation/sac:Ad
ditionalProperty/cbc:ID (Código del concepto - Catálogo No. 15)
an3 n(3) /Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sac:AdditionalInformation/sac:Ad
ditionalProperty/cbc:Value (Valor del concepto)
```

##### 4

```
Número de cuenta del proveedor en
el Banco de la Nación Global^ C^
```

```
an4 /Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sac:AdditionalInformation/sac:Ad
ditionalProperty/cbc:ID (Código del concepto - Catálogo No. 15)
n11 n(11) /Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sac:AdditionalInformation/sac:Ad
ditionalProperty/cbc:Value (Valor del concepto)
```

##### 5

```
Valor referencial del servicio de
transp.bienes por vía terrestre, de
conformidad con DS N°010- 2006 -
MTC, que aprobó la Tabla de Valores
Referenciales para la aplicación del
Sistema al servicio de transporte de
bienes realizado por vía terrestre.
```

```
Global C
```

```
an4 /Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sac:AdditionalInformation/sac:Ad
ditionalMonetaryTotal/cbc:ID (Código del tipo de elemento - Catálogo No. 14)
an...15 n(12,2) /Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sac:AdditionalInformation/sac:Ad
ditionalMonetaryTotal/sac:ReferenceAmount (Valor referencial )
```

##### 6

```
Nombre y matrícula de la embarcación
pesquera utilizada para efectuar la
extracción y descarga de los bienes
vendidos, en los casos que se hubiera
utilizado dicho medio
```

```
Global C
```

```
an4 /Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sac:AdditionalInformation/sac:Ad
ditionalProperty/cbc:ID (Código del concepto - Catálogo No. 15)
an...100 /Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sac:AdditionalInformation/sac:Ad
ditionalProperty/cbc:Value (Valor del concepto)
```

```
7 Descripción del tipo y cantidad de la
especie vendida
```

```
Global C
```

```
an4 /Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sac:AdditionalInformation/sac:Ad
ditionalProperty/cbc:ID (Código del concepto - Catálogo No. 15)
an...150 /Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sac:AdditionalInformation/sac:Ad
ditionalProperty/cbc:Value (Valor del concepto)
```

##### 8

```
Lugar de la descarga Global C
```

```
an4 /Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sac:AdditionalInformation/sac:Ad
ditionalProperty/cbc:ID (Código del concepto - Catálogo No. 15)
an..100 /Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sac:AdditionalInformation/sac:Ad
ditionalProperty/cbc:Value (Valor del concepto)
```

**9**
Fecha de la descarga
Global
C

an4 (^) /Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sac:AdditionalInformation/sac:Ad
ditionalProperty/cbc:ID (Código del concepto - Catálogo No. 15)
an..10 YYYY-MM-DD (^) /Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sac:AdditionalInformation/sac:Ad
ditionalProperty/cbc:Value (Valor del concepto)

### 1.2 Ejemplo de una factura con un concepto de detracción

```
Elemento Valor
```

Valor de Venta 20,

IGV 3,

Importe total de la venta 24,

Porcentaje de detracción - Recursos

Hidrobiológicos

```
9 %
```

Monto de la detracción 2 ,208.

Código de bb y ss sujetos a detracción 004 Recursos hidrobiológicos

Numero de Cta en el Bco. Nac. 192 - 99982 - 1

Recursos Hidrobiológicos - Nombre y

matrícula de la embarcación

```
“ADITA 3”, Matricula: IO- 2393 - PM
```

Recursos Hidrobiológicos - Tipo y cantidad

de especie vendida

```
185.85 TM de Anchoveta blanca
```

Recursos Hidrobiológicos - Lugar de

descarga

```
Planta Pesquera de PESQUERA
```

```
DIAMANTE S.A, Puerto Mollendo
```

Recursos Hidrobiológicos-Fecha de

descarga (aa/mm/dd)

```
2012 - 10 - 09
```

<Invoice>

.........

<ext:UBLExtensions>
<ext:UBLExtension>
<ext:ExtensionContent>
<sac:AdditionalInformation>
<sac:AdditionalMonetaryTotal>
<cbc:ID> 1001 </cbc:ID>
<cbc:PayableAmount currencyID="PEN"> 20800 .00</cbc:PayableAmount>
</sac:AdditionalMonetaryTotal>
<sac:AdditionalMonetaryTotal>
<cbc:ID>2003</cbc:ID>
<cbc:PayableAmount currencyID="PEN">2208.96</cbc:PayableAmount>
<sac:Percent>9.00%</sac:Percent>
</sac:AdditionalMonetaryTotal>
<sac:AdditionalProperty>
<cbc:ID> 3000 </cbc:ID>
<cbc:Value> 004 </cbc:Value>
</sac:AdditionalProperty>
<sac:AdditionalProperty>
<cbc:ID>3001</cbc:ID>
<cbc:Value>192- 99982 - 1</cbc:Value>
</sac:AdditionalProperty>
<sac:AdditionalProperty>
<cbc:ID>3002</cbc:ID>
<cbc:Value>“ADITA 3”, Matricula: IO- 2393 - PM</cbc:Value>
</sac:AdditionalProperty>
<sac:AdditionalProperty>
<cbc:ID>3003</cbc:ID>
<cbc:Value>185.85 TM de anchoveta blanca</cbc:Value>
</sac:AdditionalProperty>
<sac:AdditionalProperty>
<cbc:ID>3004</cbc:ID>
<cbc:Value> Planta Pesquera de PESQUERA DIAMANTE S.A, Puerto Mollendo
</cbc:Value>
</sac:AdditionalProperty>
<sac:AdditionalProperty>
<cbc:ID>3005</cbc:ID>
<cbc:Value>2012- 10 - 09 </cbc:Value>
</sac:AdditionalProperty>
</sac:AdditionalInformation>
</ext:ExtensionContent>
</ext:UBLExtension>
</ext:UBLExtensions>
...
<cac:TaxTotal>
<cbc:TaxAmount currencyID="PEN"> 3744. 00 </cbc:TaxAmount>
<cac:TaxSubtotal>
<cbc:TaxAmount currencyID="PEN"> 3744. 00 </cbc:TaxAmount>
<cac:TaxCategory>
<cac:TaxScheme>
<cbc:ID>1000</cbc:ID>
<cbc:Name>IGV</cbc:Name>
<cbc:TaxTypeCode>VAT</cbc:TaxTypeCode>
</cac:TaxScheme>
</cac:TaxCategory>
</cac:TaxSubtotal>
</cac:TaxTotal>
<cac:LegalMonetaryTotal>
<cbc:PayableAmount currencyID="PEN">24544.00</cbc:PayableAmount>
</cac:LegalMonetaryTotal>
...
</Invoice>

## 2 SERVICIOS DE HOSPEDAJE

Este concepto tributario, que incluye servicio de hospedaje y alimentación, es considerado una

operación de exportación para efectos del IGV, y cuenta con un beneficio tributario (saldo a

Favor del Exportador, materia de beneficio).

Por tal motivo, se solicita información adicional, relacionada con el turista y/o agencia de viajes

según corresponda, la misma que se proporciona a través del PDB – exportadores.

En este contexto en este rubro se definen los elementos (tag ́s) a utilizar para la identificación

y/o construcción de datos relacionados con el Servicio de hospedaje, de manera opcional, en la

factura electrónica.

### 2.1 Forma de consignar la información.

```
En los puntos 2.2 y 2.3 se especifican los elementos necesarios para consignar la
```

```
información, en la factura electrónica, según se trate de un servicio de hospedaje
```

```
prestado directamente o prestado a través de una agencia de viajes.
```

```
Asimismo, se requiere utilizar los conceptos y elementos codificados en el anexo 15 de
```

```
la Resolución de Superintendencia 097-2012/SUNAT y modificatorias.
```

### 2.2 Servicio de hospedaje.

```
Para este concepto utilizar el tag ya definido para la descripción del bien o servicio.
```

```
Concepto Tag UBL nivel Condición
informática
```

```
Tipo y
longitud
```

```
Formato
```

```
Descripción
detallada
```

```
Para este rubro utilizar ya
definido en el anexo 9
(/Factura/ ítems N°11,12,13)
```

```
Según lo indicado anexo 9 (/Factura/ para los ítems
N°11,12,13)
```

### 2.3 Servicio de alimentación.-

#### A. En caso este servicio sea prestado directamente al sujeto no domiciliado....

Concepto Tag UBL nivel Condición
informática

```
Tipo y
longitud
```

```
Formato
```

1 Tipo y número de
documento del sujeto
no domiciliado.

```
Para este rubro utilizar ya definido en el
anexo 9 (/Factura/ ítem N° 9 )
```

```
Según lo indicado anexo 9 (/Factura/ para los
ítems N°9)
```

2 Apellidos y nombres
del sujeto no
domiciliado

```
Para este rubro utilizar ya definido en el
anexo 9 (/Factura/ ítem N°10)
```

```
Según lo indicado anexo 9 (/Factura/ para los
ítems N°10)
```

3 Cantidad y detalle de
los alimentos y bebidas
consumidos. En caso el
establecimiento ofrezca
bufés, menús o
similares sólo se
precisará la cantidad y
denominación de
dichos conceptos.

```
Para este rubro utilizar ya definido en el
anexo 9 (/Factura/ ítems N°11,12,13)
```

```
Según lo indicado anexo 9 (/Factura/ para los
ítems N°11,12,13)
```

4 Importes totales de los
alimentos y bebidas
consumidos.

```
Para este rubro utilizar ya definido en el
anexo 9 (/Factura/ ítem N° 19 )
```

```
Según lo indicado anexo 9 (/Factura/ para los
ítems N° 19 )
```

5 Fecha de ingreso al
país según pasaporte

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ex
t:ExtensionContent/sac:AdditionalInformation/s
ac:AdditionalProperty/cbc:ID (Código del
concepto - Catálogo No. 15)
```

```
Global C n
```

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ex
t:ExtensionContent/sac:AdditionalInformation/s
ac:AdditionalProperty/cbc:Value (Valor del
concepto)
```

```
an..
yyyy-mm-dd
```

6 Fecha de ingreso al
establecimientode
hospedaje

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ex
t:ExtensionContent/sac:AdditionalInformation/s
ac:AdditionalProperty/cbc:ID (Código del
concepto - Catálogo No. 15)
```

```
Global C n
```

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ex
t:ExtensionContent/sac:AdditionalInformation/s
ac:AdditionalProperty/cbc:Value (Valor del
concepto)
```

```
an..10 yyyy-mm-dd
```

7 Fecha de salida del
establecimiento de
hospedaje

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ex
t:ExtensionContent/sac:AdditionalInformation/s
ac:AdditionalProperty/cbc:ID (Código del
concepto - Catálogo No. 15)
```

```
Global C n
```

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ex
t:ExtensionContent/sac:AdditionalInformation/s
ac:AdditionalProperty/cbc:Value (Valor del
concepto)
```

```
an..10 yyyy-mm-dd
```

8 Número de días de
permanencia

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ex
t:ExtensionContent/sac:AdditionalInformation/s
ac:AdditionalProperty/cbc:ID (Código del
concepto - Catálogo No. 15)
```

```
Global C n
```

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ex
t:ExtensionContent/sac:AdditionalInformation/s
ac:AdditionalProperty/cbc:Value (Valor del
concepto)
```

```
n 2 n(2)
```

9 Código país de emisión
del pasaporte

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ex
t:ExtensionContent/sac:AdditionalInformation/s
ac:AdditionalProperty/cbc:ID (Código del
concepto - Catálogo No. 15)
```

```
Global C n
```

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ex
t:ExtensionContent/sac:AdditionalInformation/s
ac:AdditionalProperty/cbc:Value (Código de país
```

- Catálogo No. 04)

```
an
```

##### 1

##### 0

```
Código país de
residencia del sujeto no
domiciliado
```

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ex
t:ExtensionContent/sac:AdditionalInformation/s
ac:AdditionalProperty/cbc:ID (Código del
concepto - Catálogo No. 15)
```

```
Global C n
```

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ex
t:ExtensionContent/sac:AdditionalInformation/s
ac:AdditionalProperty/cbc:Value (Código de país
```

- Catálogo No. 04

```
an
```

#### B. En caso este servicio sea prestado a un sujeto no domiciliado que opte por un

#### paquete turístico

Concepto^ Tag UBL^ nivel^ Condición
informática

```
Tipo y
longitud
```

```
Formato
```

1 Número de RUC de
la Agencia de Viajes
y Turismo

```
Para este rubro utilizar lo definido en el anexo
9 (/Factura/ ítem N°6)
```

```
Según lo indicado anexo 9 (/Factura/ para los
ítems N°6)
```

2 Apellidos y nombres
o denominación
social de la Agencia
de Viajes y Turismo

```
Para este rubro utilizar lo definido en el anexo
9 (/Factura/ ítem N°3)
```

```
Según lo indicado anexo 9 (/Factura/ para los
ítems N°3)
```

3 Tipo de documento
de identidad del
sujeto no domiciliado

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:
ExtensionContent/sac:AdditionalInformation/sac:A
dditionalProperty/cbc:ID (Código del concepto -
Catálogo No. 15)
```

```
Global
C
n
```

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:
ExtensionContent/sac:AdditionalInformation/sac:A
dditionalProperty/cbc:Value (Valor del concepto).
Ver catálogo N°
```

```
An 1
```

4 Número de
documento del sujeto
no domiciliado.

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:
ExtensionContent/sac:AdditionalInformation/sac:A
dditionalProperty/cbc:ID (Código del concepto -
Catálogo No. 15)
```

```
Global
C
n
```

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:
ExtensionContent/sac:AdditionalInformation/sac:A
dditionalProperty/cbc:Value (Valor del concepto)
```

```
An..
```

5 Nombres y apellidos
del sujeto no
domiciliado

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:
ExtensionContent/sac:AdditionalInformation/sac:A
dditionalProperty/cbc:ID (Código del concepto -
Catálogo No. 15)
```

```
Global
C
n
```

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:
ExtensionContent/sac:AdditionalInformation/sac:A
dditionalProperty/cbc:Value (Valor del concepto)
```

```
An..
```

6 Cantidad y detalle de
los alimentos y
bebidas consumidos.
En caso el
establecimiento
ofrezca bufés, menús
o similares sólo se
precisará la cantidad
y denominación de
dichos conceptos

```
Para este rubro utilizar lo definido en el anexo
9 (/Factura/ ítems N°11,12,13)
```

```
Según lo indicado anexo 9 (/Factura/ para los
ítems N°11,12,13)
```

7 Importes totales de
los alimentos y
bebidas consumidos

```
Para este rubro utilizar ya definido en el anexo
9 (/Factura/ ítem N° 19 )
```

```
Según lo indicado anexo 9 (/Factura/ para los
ítems N° 19 )
```

8 Fecha de ingreso al
país según pasaporte

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:
ExtensionContent/sac:AdditionalInformation/sac:A
dditionalProperty/cbc:ID (Código del concepto -
Catálogo No. 15)
```

```
Global
C
n
```

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:
ExtensionContent/sac:AdditionalInformation/sac:A
dditionalProperty/cbc:Value (Valor del concepto)
```

```
an..
yyyy-mm-
dd
```

9 Fecha de ingreso al
establecimiento de
hospedaje

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:
ExtensionContent/sac:AdditionalInformation/sac:A
dditionalProperty/cbc:ID (Código del concepto -
Catálogo No. 15)
```

```
Global
C
n
```

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:
ExtensionContent/sac:AdditionalInformation/sac:A
dditionalProperty/cbc:Value (Valor del concepto)
```

```
an..
yyyy-mm-
dd
```

10 Fecha de salida del
establecimiento de
hospedaje

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:
ExtensionContent/sac:AdditionalInformation/sac:A
dditionalProperty/cbc:ID (Código del concepto -
Catálogo No. 15)
```

```
Global C n
```

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:
ExtensionContent/sac:AdditionalInformation/sac:A
dditionalProperty/cbc:Value (Valor del concepto)
```

```
an..10 yyyy-mm-
dd
```

11 Número de días de
permanencia

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:
ExtensionContent/sac:AdditionalInformation/sac:A
dditionalProperty/cbc:ID (Código del concepto -
Catálogo No. 15)
```

```
Global
C
n
```

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:
ExtensionContent/sac:AdditionalInformation/sac:A
dditionalProperty/cbc:Value (Valor del concepto)
```

```
n 2
n(2)
```

12 Código país de
emisión del pasaporte

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:
ExtensionContent/sac:AdditionalInformation/sac:A
dditionalProperty/cbc:ID (Código del concepto -
Catálogo No. 15)
```

```
Global
C
n
```

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:
ExtensionContent/sac:AdditionalInformation/sac:A
dditionalProperty/cbc:Value (Código de país -
Catálogo No. 04)
```

```
an
```

13 Código país de
residencia del sujeto
no domiciliado

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:
ExtensionContent/sac:AdditionalInformation/sac:A
dditionalProperty/cbc:ID (Código del concepto -
Catálogo No. 15)
```

```
Global
C
n
```

```
/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:
ExtensionContent/sac:AdditionalInformation/sac:A
dditionalProperty/cbc:Value (Código de país -
Catálogo No. 04)
```

```
an
```

(^14) Leyenda “Agencia de
Viaje - Paquete
turístico”
/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:
ExtensionContent/sac:AdditionalInformation/sac:A
dditionalProperty/cbc:ID (Código del concepto -
Catálogo No. 15)
Global C an
/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:
ExtensionContent/sac:AdditionalInformation/sac:A
dditionalProperty/cbc:Value (Valor del concepto)
Global C an.. (^)

### 2.4 Ejemplo - Servicio hospedaje Paquete Turístico

```
El Hotel Casa de los Andes SAC inscrito en el Registro de Hospedajes identificado con
```

```
RUC: 20505670443, con domicilio fiscal en Av. Miraflores 777, San Isidro – Lima -
```

```
Perú, emite una factura por servicios de hospedaje y alimentación con los siguiente
```

```
datos:
```

```
Elemento Valor
Numero de factura F021- 4370
Fecha de emisión 30/07/2 010
Numero de pasaporte del sujeto no domiciliado N
Apellidos y nombres del sujeto no domiciliado Herman Rosemery
Hospedaje 2000 USD
Cantidad y detalle de los alimentos y bebidas
consumidos.
```

```
4 CENAS. El importe por cena = 200 USD
```

```
Importes totales de los alimentos y bebidas
consumidos
```

##### 800 USD

```
Fecha de ingreso al país según pasaporte 19/07/
Fecha de ingreso al establecimiento de
hospedaje
```

##### 19/07/

```
Fecha de salida del establecimiento de hospedaje 29/07/
Número de días de permanencia 10
País de emisión del pasaporte Australia
País de residencia del sujeto no domiciliado Australia
Número de RUC de la Agencia de Viajes y
Turismo
```

##### 20101010181

```
Apellidos y nombres o denominación social de la
Agencia de Viajes y Turismo
```

##### TURISMO PERU S .A.

<?xml version="1.0" encoding="ISO- 8859 - 1" standalone="no"?><Invoice

xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
xmlns:ccts="urn:un:unece:uncefact:documentation:2"
xmlns:ds="http://www.w3.org/2000/09/xmldsig#"
xmlns:ext="urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
xmlns:qdt="urn:oasis:names:specification:ubl:schema:xsd:QualifiedDatatypes-2"
xmlns:sac="urn:sunat:names:specification:ubl:peru:schema:xsd:SunatAggregateComponents-1"
xmlns:udt="urn:un:unece:uncefact:data:specification:UnqualifiedDataTypesSchemaModule:2"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<ext:UBLExtensions>
<ext:UBLExtension>
<ext:ExtensionContent>
<sac:AdditionalInformation>
<sac:AdditionalMonetaryTotal>
<cbc:ID>1002</cbc:ID>
<cbc:PayableAmount currencyID="USD">2800.00</cbc:PayableAmount>
</sac:AdditionalMonetaryTotal>
<sac:AdditionalProperty>
<cbc:ID>4002</cbc:ID>
<cbc:Value>2010- 07 - 19</cbc:Value>
</sac:AdditionalProperty>
<sac:AdditionalProperty>
<cbc:ID>4003</cbc:ID>
<cbc:Value>2010- 07 - 19</cbc:Value>
</sac:AdditionalProperty>
<sac:AdditionalProperty>
<cbc:ID>4004</cbc:ID>
<cbc:Value>2010- 07 - 29</cbc:Value>
</sac:AdditionalProperty>
<sac:AdditionalProperty>
<cbc:ID>4005</cbc:ID>
<cbc:Value>10</cbc:Value>
</sac:AdditionalProperty>
<sac:AdditionalProperty>
<cbc:ID>4000</cbc:ID>
<cbc:Value>AU</cbc:Value>
</sac:AdditionalProperty>
<sac:AdditionalProperty>
<cbc:ID>4001</cbc:ID>
<cbc:Value>AU</cbc:Value>
</sac:AdditionalProperty>
<sac:AdditionalProperty>
<cbc:ID>2004</cbc:ID>
<cbc:Value>Agencia de Viaje - Paquete turístico</cbc:Value>
</sac:AdditionalProperty>
<sac:AdditionalProperty>
<cbc:ID>4007</cbc:ID>
<cbc:Value>Herman Rosemery</cbc:Value>
</sac:AdditionalProperty>
<sac:AdditionalProperty>
<cbc:ID>4008</cbc:ID>
<cbc:Value> 7</cbc:Value>
</sac:AdditionalProperty>
<sac:AdditionalProperty>
<cbc:ID>4009</cbc:ID>
<cbc:Value>N5234918</cbc:Value>
</sac:AdditionalProperty>
</sac:AdditionalInformation>
</ext:ExtensionContent>
</ext:UBLExtension>
<ext:UBLExtension><ext:ExtensionContent><ds:Signature
Id="signatureKG"><ds:SignedInfo><ds:CanonicalizationMethod
Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/><ds:SignatureMethod
Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1"/><ds:Reference
URI=""><ds:Transforms><ds:Transform
Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-
signature"/></ds:Transforms><ds:DigestMethod
Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"/><ds:DigestValue>MSCkgGbi0XipGIpVW3dr
pQ7AH6A=</ds:DigestValue></ds:Reference></ds:SignedInfo><ds:SignatureValue>HrdZ57CanVVfi
DyBzxzDi+KKapX/9+P6QIvJ7OM5JXW791RR9FjzhiJpBfX402KJpdE+fLUIx3Fw
Mlao4/hqPhyqq6QWQE07WCU7qpDYkbrbE1+Zm8SYwHyiUSwiRIvzsIvuOMUCzN9UGwqPV81OZbBI
Kmir/axfJOk1qHYVKuA=</ds:SignatureValue><ds:KeyInfo><ds:X509Data><ds:X509SubjectName>1.
.840.113549.1.9.1=#161a4253554c434140534f55544845524e504552552e434f4d2e5045,CN=Juan
Robles,OU=20505670443,O=Hotel Casa de los Andes

SAC,L=LIMA,ST=LIMA,C=PE</ds:X509SubjectName><ds:X509Certificate>MIIESTCCAzGgAwIBAgIKWOCR
zgAAAAAAIjANBgkqhkiG9w0BAQUFADAnMRUwEwYKCZImiZPyLGQB
GRYFU1VOQVQxDjAMBgNVBAMTBVNVTkFUMB4XDTEwMTIyODE5NTExMFoXDTExMTIyODIwMDExMFow
gZUxCzAJBgNVBAYTAlBFMQ0wCwYDVQQIEwRMSU1BMQ0wCwYDVQQHEwRMSU1BMREwDwYDVQQKEwhT
T1VUSEVSTjEUMBIGA1UECxMLMjAxMDAxNDc1MTQxFDASBgNVBAMTC0JvcmlzIFN1bGNhMSkwJwYJ
KoZIhvcNAQkBFhpCU1VMQ0FAU09VVEhFUk5QRVJVLkNPTS5QRTCBnzANBgkqhkiG9w0BAQEFAAOB
jQAwgYkCgYEAtRtcpfBLzyajuEmYt4mVH8EE02KQiETsdKStUThVYM7g3Lkx5zq3SH5nLH00EKGC
tota6RR+V40sgIbnh+Nfs1SOQcAohNwRfWhho7sKNZFR971rFxj4cTKMEvpt8Dr98UYFkJhph6Wn
sniGM2tJDq9KJ52UXrlScMfBityx0AsCAwEAAaOCAYowggGGMA4GA1UdDwEB/wQEAwIE8DBEBgkq
hkiG9w0BCQ8ENzA1MA4GCCqGSIb3DQMCAgIAgDAOBggqhkiG9w0DBAICAIAwBwYFKw4DAgcwCgYI
KoZIhvcNAwcwHQYDVR0OBBYEFG/m6twbiRNzRINavjq+U0j/sZECMBMGA1UdJQQMMAoGCCsGAQUF
BwMCMB8GA1UdIwQYMBaAFN9kHQDqWONmozw3xdNSIMFW2t+7MFkGA1UdHwRSMFAwTqBMoEqGImh
dHA6Ly9wY2IyMjYvQ2VydEVucm9sbC9TVU5BVC5jcmyGJGZpbGU6Ly9cXHBjYjIyNlxDZXJ0RW5y
b2xsXFNVTkFULmNybDB+BggrBgEFBQcBAQRyMHAwNQYIKwYBBQUHMAKGKWh0dHA6Ly9wY2IyMjYv
Q2VydEVucm9sbC9wY2IyMjZfU1VOQVQuY3J0MDcGCCsGAQUFBzAChitmaWxlOi8vXFxwY2IyMjZc
Q2VydEVucm9sbFxwY2IyMjZfU1VOQVQuY3J0MA0GCSqGSIb3DQEBBQUAA4IBAQBI6wJ/QmRpz3C
rorBflOvA9DOa3GNiiB7rtPIjF4mPmtgfo2pK9gvnxmV2pST3ovfu0nbG2kpjzzaaelRjEodHvkc
M3abGsOE53wfxqQF5uf/jkzZA9hbLHtE1aLKBD0Mhzc6cvI072alnE6QU3RZ16ie9CYsHmMrs+sP
HMy8DJU5YrdnqHdSn2D3nhKBi4QfT/WURPOuo6DF4iWgrCyMf3eJgmGKSUN3At5fK4HSpfyURT0k
boaJKNBgQwy0HhGh5BLM7DsTi/KwfdUYkoFgrY71Pm23+ra+xTow1Vk9gj5NqrlpMY5gAVQXEIo
++GxDtaK/5EiVKSqzJ6geIfz</ds:X509Certificate></ds:X509Data></ds:KeyInfo></ds:Signature><
/ext:ExtensionContent></ext:UBLExtension></ext:UBLExtensions>
<cbc:UBLVersionID>2.0</cbc:UBLVersionID>
<cbc:CustomizationID>1.0</cbc:CustomizationID>
<cbc:ID>F021-4370</cbc:ID>
<cbc:IssueDate>2012- 10 - 19</cbc:IssueDate>
<cbc:InvoiceTypeCode>01</cbc:InvoiceTypeCode>
<cbc:DocumentCurrencyCode>USD</cbc:DocumentCurrencyCode>
<cac:Signature>
<cbc:ID>IDSignKG</cbc:ID>
<cac:SignatoryParty>
<cac:PartyIdentification>
<cbc:ID>20505670443</cbc:ID>
</cac:PartyIdentification>
<cac:PartyName>
<cbc:Name> Hotel Casa de los Andes SAC </cbc:Name>
</cac:PartyName>
</cac:SignatoryParty>
<cac:DigitalSignatureAttachment>
<cac:ExternalReference>
<cbc:URI>#SignST</cbc:URI>
</cac:ExternalReference>
</cac:DigitalSignatureAttachment>
</cac:Signature>
<cac:AccountingSupplierParty>
<cbc:CustomerAssignedAccountID>20505670443</cbc:CustomerAssignedAccountID>
<cbc:AdditionalAccountID>6</cbc:AdditionalAccountID>
<cac:Party>
<cac:PostalAddress>
<cbc:ID>150122</cbc:ID>
<cbc:StreetName>Av. Miraflores 777</cbc:StreetName>
<cbc:CityName>LIMA</cbc:CityName>
<cbc:CountrySubentity>LIMA</cbc:CountrySubentity>
<cbc:District>SAN ISIDRO</cbc:District>
<cac:Country>
<cbc:IdentificationCode>PE</cbc:IdentificationCode>
</cac:Country>
</cac:PostalAddress>
<cac:PartyLegalEntity>
<cbc:RegistrationName> Hotel Casa de los Andes SAC </cbc:RegistrationName>
</cac:PartyLegalEntity>
</cac:Party>
</cac:AccountingSupplierParty>
<cac:AccountingCustomerParty>
<cbc:CustomerAssignedAccountID>20101010181</cbc:CustomerAssignedAccountID>
<cbc:AdditionalAccountID>6</cbc:AdditionalAccountID>
<cac:Party>
<cac:PartyLegalEntity>
<cbc:RegistrationName>TURISMO PERU SA</cbc:RegistrationName>
</cac:PartyLegalEntity>
</cac:Party>
</cac:AccountingCustomerParty>
<cac:TaxTotal>
<cbc:TaxAmount currencyID="USD">0.00</cbc:TaxAmount>
<cac:TaxSubtotal>
<cbc:TaxAmount currencyID="USD">0.00</cbc:TaxAmount>
<cac:TaxCategory>

<cac:TaxScheme>
<cbc:ID>1000</cbc:ID>
<cbc:Name>IGV</cbc:Name>
<cbc:TaxTypeCode>VAT</cbc:TaxTypeCode>
</cac:TaxScheme>
</cac:TaxCategory>
</cac:TaxSubtotal>
</cac:TaxTotal>
<cac:LegalMonetaryTotal>
<cbc:PayableAmount currencyID="USD">2800.00</cbc:PayableAmount>
</cac:LegalMonetaryTotal>
<cac:InvoiceLine>
<cbc:ID>1</cbc:ID>
<cbc:InvoicedQuantity unitCode="ZZ">1</cbc:InvoicedQuantity>
<cbc:LineExtensionAmount currencyID="USD">2000.00</cbc:LineExtensionAmount>
<cac:PricingReference>
<cac:AlternativeConditionPrice>
<cbc:PriceAmount currencyID="USD">2000.00</cbc:PriceAmount>
<cbc:PriceTypeCode>01</cbc:PriceTypeCode>
</cac:AlternativeConditionPrice>
</cac:PricingReference>
<cac:TaxTotal>
<cbc:TaxAmount currencyID="USD">0.00</cbc:TaxAmount>
<cac:TaxSubtotal>
<cbc:TaxAmount currencyID="USD">0.00</cbc:TaxAmount>
<cac:TaxCategory>
<cbc:TaxExemptionReasonCode>40</cbc:TaxExemptionReasonCode>
<cac:TaxScheme>
<cbc:ID>1000</cbc:ID>
<cbc:Name>IGV</cbc:Name>
<cbc:TaxTypeCode>VAT</cbc:TaxTypeCode>
</cac:TaxScheme>
</cac:TaxCategory>
</cac:TaxSubtotal>
</cac:TaxTotal>
<cac:Item>
<cbc:Description>ALOJAMIENTO</cbc:Description>
</cac:Item>
<cac:Price>
<cbc:PriceAmount currencyID="USD">2000.00</cbc:PriceAmount>
</cac:Price>
</cac:InvoiceLine>
<cac:InvoiceLine>
<cbc:ID>2</cbc:ID>
<cbc:InvoicedQuantity unitCode="ZZ">4</cbc:InvoicedQuantity>
<cbc:LineExtensionAmount currencyID="USD">800.00</cbc:LineExtensionAmount>
<cac:PricingReference>
<cac:AlternativeConditionPrice>
<cbc:PriceAmount currencyID="USD">200.00</cbc:PriceAmount>
<cbc:PriceTypeCode>01</cbc:PriceTypeCode>
</cac:AlternativeConditionPrice>
</cac:PricingReference>
<cac:TaxTotal>
<cbc:TaxAmount currencyID="USD">0.00</cbc:TaxAmount>
<cac:TaxSubtotal>
<cbc:TaxAmount currencyID="USD">0.00</cbc:TaxAmount>
<cac:TaxCategory>
<cbc:TaxExemptionReasonCode>40</cbc:TaxExemptionReasonCode>
<cac:TaxScheme>
<cbc:ID>1000</cbc:ID>
<cbc:Name>IGV</cbc:Name>
<cbc:TaxTypeCode>VAT</cbc:TaxTypeCode>
</cac:TaxScheme>
</cac:TaxCategory>
</cac:TaxSubtotal>
</cac:TaxTotal>
<cac:Item>
<cbc:Description>CENAS</cbc:Description>
</cac:Item>
<cac:Price>
<cbc:PriceAmount currencyID="USD">800.00</cbc:PriceAmount>
</cac:Price>
</cac:InvoiceLine>
</Invoice>
