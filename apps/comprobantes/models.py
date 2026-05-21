from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from apps.empresas.models import Empresa
from apps.clientes.models import Cliente


class SerieComprobante(models.Model):
    TIPO_CHOICES = [
        ('01', 'Factura'),
        ('03', 'Boleta'),
        ('07', 'Nota de Crédito'),
        ('08', 'Nota de Débito'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='series')
    tipo = models.CharField(max_length=2, choices=TIPO_CHOICES)
    serie = models.CharField(max_length=4)
    correlativo_actual = models.PositiveIntegerField(default=0)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Serie de Comprobante"
        verbose_name_plural = "Series de Comprobantes"
        unique_together = ['empresa', 'tipo', 'serie']
        ordering = ['empresa', 'tipo', 'serie']

    def __str__(self):
        return f"{self.empresa.ruc}-{self.tipo}-{self.serie}"

    def siguiente_correlativo(self):
        with models.Q.objects.filter(pk=self.pk).select_for_update():
            self.correlativo_actual += 1
            self.save(update_fields=['correlativo_actual'])
            return self.correlativo_current


class Comprobante(models.Model):
    ESTADO_CHOICES = [
        ('BORRADOR', 'Borrador'),
        ('EMITIDO', 'Emitido'),
        ('ENVIADO', 'Enviado'),
        ('ACEPTADO', 'Aceptado'),
        ('RECHAZADO', 'Rechazado'),
        ('ANULADO_PARCIAL', 'Anulado Parcial'),
        ('ANULADO_TOTAL', 'Anulado Total'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name='comprobantes')
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='comprobantes')
    serie = models.ForeignKey(SerieComprobante, on_delete=models.PROTECT)
    numero = models.PositiveIntegerField()
    fecha = models.DateField()
    tipo = models.CharField(max_length=2, choices=SerieComprobante.TIPO_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='BORRADOR')
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    igv = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    xml_firmado = models.TextField(blank=True, null=True)
    zip_path = models.CharField(max_length=500, blank=True, null=True)
    sunat_ticket = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Comprobante"
        verbose_name_plural = "Comprobantes"
        ordering = ['-fecha', '-created_at']
        unique_together = ['serie', 'numero']

    def __str__(self):
        return f"{self.serie.serie}-{self.numero:08d}"

    def calcular_totales(self):
        """
        Calcula y actualiza los importes del comprobante electrónico: subtotal, igv y total.
        Realiza el cálculo de impuestos de forma individual para cada línea de detalle,
        y luego los acumula a nivel de cabecera.
        
        Asegura que todos los cálculos se realicen utilizando tipos decimal.Decimal
        para prevenir errores de precisión y el error de tipos al multiplicar por float.
        """
        from decimal import Decimal
        detalles = self.detalles.all()
        subtotal = Decimal('0.00')
        igv_total = Decimal('0.00')
        tasa_igv = Decimal(str(settings.IGV_TASA))
        
        for detalle in detalles:
            # Multiplicación exacta usando Decimal en el detalle
            base = detalle.precio_unitario * detalle.cantidad
            if detalle.afecto_igv:
                # Multiplicación de Decimal por la tasa también en Decimal
                igv_linea = round(base * tasa_igv, 2)
            else:
                igv_linea = Decimal('0.00')
            
            detalle.subtotal = base
            detalle.igv_linea = igv_linea
            detalle.save()
            
            subtotal += base
            igv_total += igv_linea
            
        self.subtotal = subtotal
        self.igv = igv_total
        self.total = subtotal + igv_total
        self.save(update_fields=['subtotal', 'igv', 'total'])

    @property
    def nombre_xml(self):
        tipo = self.tipo or (self.serie.tipo if self.serie else '')
        return f"{self.empresa.ruc}-{tipo}-{self.serie.serie}-{self.numero:08d}.xml"

    @property
    def nombre_zip(self):
        tipo = self.tipo or (self.serie.tipo if self.serie else '')
        return f"{self.empresa.ruc}-{tipo}-{self.serie.serie}-{self.numero:08d}.zip"


class DetalleComprobante(models.Model):
    comprobante = models.ForeignKey(Comprobante, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey('productos.Producto', on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=12, decimal_places=4)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=4)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    afecto_igv = models.BooleanField(default=True)
    cod_tipo_afectacion = models.CharField(max_length=10, default='10')
    igv_linea = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Detalle de Comprobante"
        verbose_name_plural = "Detalles de Comprobante"

    def __str__(self):
        return f"{self.comprobante} - {self.producto.codigo}"


class LogEnvioSUNAT(models.Model):
    comprobante = models.ForeignKey(Comprobante, on_delete=models.CASCADE, related_name='logs')
    fecha_envio = models.DateTimeField(auto_now_add=True)
    estado_respuesta = models.CharField(max_length=20)
    codigo_respuesta = models.CharField(max_length=10)
    descripcion = models.TextField()
    uuid = models.CharField(max_length=100, blank=True, null=True)
    cdr_xml = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Log de Envío SUNAT"
        verbose_name_plural = "Logs de Envío SUNAT"
        ordering = ['-fecha_envio']

    def __str__(self):
        return f"{self.comprobante} - {self.codigo_respuesta}"


class ImportacionComprobante(models.Model):
    archivo_csv = models.FileField(upload_to='importaciones/')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    fecha_importacion = models.DateTimeField(auto_now_add=True)
    total_registros = models.PositiveIntegerField(default=0)
    importados_exitosos = models.PositiveIntegerField(default=0)
    errores = models.PositiveIntegerField(default=0)
    estado = models.CharField(
        max_length=20,
        choices=[
            ('PROCESANDO', 'Procesando'),
            ('COMPLETADO', 'Completado'),
            ('ERROR', 'Error'),
        ],
        default='PROCESANDO'
    )
    log_errores = models.TextField(blank=True)

    class Meta:
        verbose_name = "Importación de Comprobante"
        verbose_name_plural = "Importaciones de Comprobantes"
        ordering = ['-fecha_importacion']

    def __str__(self):
        return f"Importación {self.id} - {self.fecha_importacion.strftime('%Y-%m-%d %H:%M')}"