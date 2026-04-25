> **ANEXO** **XIII**
>
> **Anexo** **B:** **Aspectos** **técnicos** **-** **emisor**
> **electrónico**
>
> **Envíos** **al** **Operador** **de** **Servicios** **Electrónicos**
>
> **1.** **Métodos** **para** **el** **envío** **mediante** **el**
> **servicio** **web**
>
> El envío se realiza a través de servicio web si se usa alguno de los
> métodos siguientes:
>
> a\) *SendBill*, el cual permite recibir un archivo ZIP con un único
> formato digital y devuelve un archivo ZIP que contiene la Constancia
> de Recepción emitido por el OSE (CDR - OSE).
>
> b\) *SendSummary*, el cual permite recibir un archivo ZIP con un único
> formato digital del Resumen Diario o Comunicación de baja. Devuelve un
> ticket con el que posteriormente, utilizando el método *GetStatus*, se
> puede obtener el archivo ZIP que contiene el CDR - OSE.
>
> c\) *GetStatus*, el cual permite recibir el ticket como parámetro y
> devuelve un objeto que indica el estado del proceso y en caso de haber
> terminado, devuelve adjunto el CDR - OSE.
>
> El servicio web deberá estar protegido vía SSL y la dirección será
> comunicada por el Operador de Servicios Electrónicos.
>
> **2.** **Sobre** **el** **empaquetado** **y** **nombres** **de**
> **los** **archivos** **generados**
>
> a\) El formato digital con la firma digital debe ser empaquetado en un
> archivo ZIP antes de su envío al OSE.
>
> b\) Nombre del formato digital y del archivo ZIP
>
> El formato digital y el archivo ZIP que contiene al primero debe ser
> generado con los nombres que se detallan a continuación:
>
> **b.1)** **Factura** **electrónica,** **boleta** **de** **venta**
> **electrónica,las** **notas** **electrónicas,** **la** **guía** **de**
> **remisión** **electrónica,** **los** **DAE** **y** **la**
> **declaración** **jurada** **informativa** **por** **contingencia**
> **enviados** **individualmente:**

||
||
||
||
||
||
||
||

||
||
||
||
||
||
||
||
||
||

> **(1)** Para el caso de los recibos electrónicos por servicios
> públicos. **(2)** Para el caso de guías de remisión electrónicas.
>
> **(3)** Para el caso de los formatos digitales a través de los cuales
> el emisor electrónico obligado declara la información de los
> comprobantes de pago o documentos en formatos impresos y/o importados
> por imprenta autorizada, según lo regulado por el acápite 4.2.4 del
> numeral 4.2 del artículo 4° de la Resolución de Superintendencia N.º
> 300 – 2014/SUNAT y modificatorias.
>
> **b.2)** **Comunicación** **de** **baja:**

||
||
||
||
||
||
||
||
||
||

||
||
||
||
||
||
||
||

> **b.3)** **Resumen** **Diario:**

||
||
||
||
||
||
||
||
||
||
||
||
||
||
||
||

> La cantidad de documentos en formato digital que podrá contener un
> resumen es de 500 como máximo.
>
> **IMPORTANTE**: A partir del 01 de enero de 2018, considerando la
> nueva estructura del Resumen Diario, deberá enviarse en bloques de 500
> líneas. Cadabloquecorresponderáaunnúmerocorrelativo diferente. Los
> envíos soncomplementarios, esdecir,se puedeenviar más de unarchivo por
> día, ylos archivos enviados no sustituyen los anteriormenteenviados.
>
> **3.** **Sobre** **losenvíospor** **lotes**
> **alOSE–RecibosElectrónicosporServicios** **Públicos**
>
> **3.1** **Métodos** **para** **el** **envío**
>
> El envío se realizará a través del servicio web, utilizando los
> siguientes métodos asíncronos:
>
> a\) *SendPack*, el cual permitirá un archivo ZIP con un único lote.
> Devuelve un ticket con el que posteriormente, utilizando el método
> *GetStatus*, se puede obtener el archivo ZIP que contiene el CDR -
> OSE.
>
> b\) *GetStatus*, el cual permite recibir el ticket como parámetro y
> devuelve un objeto que indica el estado del proceso y en caso de haber
> terminado, devuelve adjunto el CDR - OSE.
>
> **3.2** **Validaciones** **de** **lotes**
>
> 1\. Se podrán recibir lotes de un máximo de 1000 archivos XML. 2. Los
> archivos XML de cada lote deben cumplir con lo siguiente:
>
> a\. Deben corresponder todos a una misma fecha de emisión. b. Deben
> corresponder a un mismo número de RUC.
>
> c\. Cada archivo XML deberá estar firmado por el emisor o por el PSE
> autorizado para dicho RUC.
>
> d\. La validación para cada archivo XML, incluido en cada lote, serán
> las mismas que las realizadas para los envíos unitarios de dichos
> archivos.
>
> e\. No debe existir numeración duplicada en cada lote (serie y número
> correlativo igual para más de un archivo XML por lote). De existir se
> rechaza el (los) archivo(s) XML duplicado(s).
>
> f\. El nombre de cada formato digital (archivo XML) que se enviará a
> través de un lote debe cumplir con la nomenclatura especificada en el
> acápite b.1) del inciso b) del numeral 2 del presente anexo.
>
> g\. La identificación de cada lote tendrá un correlativo por día. La
> nomenclatura será la siguiente:
>
> Ruc/prefijo de lote/fecha/correlativo
>
> 20100066603-LT-20110522-1 20100066603-LT-20110522-2
>
> El correlativo es un identificador y debe ser único.
>
> 3\. Si algún documento no cumple con lo indicado en el numeral 2, sólo
> se rechazará el archivo XML que incumple con la regla de validación,
> dejando procesar el resto de los archivos.
>
> **4.** **Sobre** **los** **envíos** **mediante** **el** **servicio**
> **web** **–** **Comprobantes** **de** **Retención** **Electrónicos**
> **y** **Comprobantes** **de** **Percepción** **Electrónicos**
>
> **4.1** **Métodos** **para** **el** **envío**
>
> El envío se realiza a través del servicio web si se usa alguno de los
> métodos siguientes:
>
> a\) *SendBill*, el cual permite recibir un archivo ZIP con un único
> documento XML de comprobante y devuelve un archivo ZIP que contiene un
> documento XML que es la constancia de aceptación o rechazo.
>
> b\) *SendSummary*, este método recibe un archivo ZIP con un único
> documento XML de comunicación del resumen diario de reversión.
> Devuelve un ticket con el que posteriormente utilizando el método
> *GetStatus* se puede obtener el archivo ZIP que contiene un documento
> XML que es la constancia de aceptación o rechazo.
>
> c\) *GetStatus*, este método recibe el ticket como parámetro y
> devuelve un objeto que indica el estado del proceso y en caso de haber
> terminado, devuelve adjunto la constancia de aceptación o rechazo.
>
> El servicio web será protegido vía SSL y la dirección será comunicada
> a través de la página web de la SUNAT.
>
> **4.2** **Seguridad** **en** **el** **envío:** ***WS-Security***
>
> Para acceder al servicio web de la SUNAT, el emisor electrónico debe
> usar el protocolo de seguridad *WS-Security*, el modelo
> *UsernameToken*, y usar como credenciales su código de usuario y la
> Clave SOL.
>
> **4.3** **Sobre** **el** **empaquetado** **y** **nombres** **de**
> **los** **archivos** **generados**
>
> a\) El formato digital con la firma digital debe ser empaquetado en un
> archivo ZIP antes de su envío a la SUNAT.
>
> b\) Nombre del formato digital y del archivo ZIP
>
> El formato digital y el archivo ZIP que contiene al primero debe ser
> generado con los nombres que se detallan a continuación:
>
> **b.1)** **Comprobante** **de** **retención** **electrónico** **y**
> **comprobante** **de** **percepción** **electrónico** **enviado**
> **individualmente:**

||
||
||
||
||
||
||
||
||
||
||

||
||
||
||
||
||
||
||

> **b.2)** **Resumen** **diario** **de** **reversión** **de** **los**
> **comprobantes** **de** **retención** **electrónicos** **y**
> **comprobantes** **de** **percepción** **electrónicos:**

||
||
||
||
||
||
||
||
||
||
||
||
||
||
||
||

> **5.** **Requisitos** **técnicos** **de** **los** **documentos**
> **electrónicos**
>
> **5.1.** **Código** **de** **barras** **QR**
>
> 5.1.1. Simbología
>
> Para la generación del código de barras QR se hará uso de la
> simbología *QR* *Code* *2005* de acuerdo a la Norma ISO/IEC
> 18004:2006. Denominada *“Information* *technology* *–* *Automatic*
> *identification* *and* *data* *capture* *techniques* *–* *QR* *Code*
> *2005* *bar* *code* *symbology* *specification”.* No debe usarse la
> variante Micro QR.
>
> 5.1.2. Características técnicas
>
> a\) Nivel de corrección de error (*Error* *Correction* *Level*): Nivel
> Q.
>
> b\) Dimensiones mínimas de los elementos del código QR:
>
> • Ancho mínimo de un módulo (*X-Dimension*): 0,0075 pulgadas (0,190
> mm).
>
> • Codificación de caracteres UTF8.
>
> 5.1.3. Información a consignar
>
> En el código de barras se consignará la información siguiente en la
> medida que exista en el comprobante de pago electrónico o en las notas
> electrónicas:
>
> a\) Número de RUC del emisor electrónico.
>
> b\) Tipo de documento.
>
> c\) Numeración conformada por serie y número correlativo.
>
> d\) Sumatoria IGV, de ser el caso.
>
> e\) Importe total de la venta, cesión en uso o servicio prestado.
>
> f\) Fecha de emisión.
>
> g\) Tipo de documento del adquirente o usuario, de ser el caso.
>
> h\) Número de documento del adquirente o usuario, de ser el caso.
>
> i\) Valor Resumen
>
> El Valor Resumen es la cadena resumen en *base* *64*, el cual es el
> resultado de aplicar el algoritmo matemático (denominado función
> *hash*) al formato XML que representa el comprobante de pago
> electrónico o notas electrónicas. Corresponde al valor del elemento
> *\<ds:DigestValue\>* del documento.
>
> La información señalada en los incisos anteriores de este numeral debe
> consignarse con el mismo formato empleado en el comprobante de pago
>
> electrónico o notas electrónicas; y, se estructura de acuerdo al
> siguiente orden, siendo el separador de campo el carácter *pipe*
> (“\|”):
>
> RUC **\|** TIPO DE DOCUMENTO **\|** SERIE **\|** NÚMERO **\|** MTO
> TOTAL IGV **\|** MTO TOTAL DEL COMPROBANTE **\|** FECHA DE EMISIÓN
> **\|** TIPO DE DOCUMENTO ADQUIRENTE **\|** NÚMERO DE DOCUMENTO
> ADQUIRENTE **\|** VALOR RESUMEN
>
> En caso del Valor Resumen, esta información podrá consignarse en la
> representación impresa, fuera del código QR.
>
> 5.1.4. Características de la Impresión
>
> La impresión debe cumplir las siguientes características:
>
> a\) Posición del código de barras dentro de la representación impresa:
> Parte inferior de la representación impresa.
>
> b\) Tamaño máximo: 6 cm de alto y 6 cm de ancho (incluye el espacio en
> blanco alrededor del código).
>
> c\) Zona de silencio mínimo (Quiet Zone) o ancho mínimo obligatorio en
> blanco alrededor del código impreso para delimitarlo: 1 mm.
>
> d\) Color de impresión: Negro.
