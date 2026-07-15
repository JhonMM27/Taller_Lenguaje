from django.db import models
from apps.core.models import ModeloBase
from apps.comprobantes.models import Comprobante


class NotaCredito(ModeloBase):
    TIPO_NC_CHOICES = [
        ('NC', 'Nota de Crédito'),
        ('NCD', 'Nota de Crédito por Descuento'),
    ]

    MOTIVO_NC = [
        ('01', 'Anulación de la operación'),
        ('06', 'Devolución por ítem'),
        ('07', 'Devolución total'),
    ]

    MOTIVO_NCD = [
        ('04', 'Descuento global'),
        ('05', 'Descuento por ítem'),
        ('08', 'Bonificación'),
    ]

    comprobante_referencia = models.ForeignKey(
        Comprobante,
        on_delete=models.PROTECT,
        related_name='notas_credito'
    )
    serie = models.CharField(max_length=4, default='FC01')
    numero = models.PositiveIntegerField(default=1)
    fecha = models.DateField(auto_now_add=True)
    tipo_nc = models.CharField(max_length=3, choices=TIPO_NC_CHOICES, default='NC')
    tipo_nota = models.CharField(max_length=2, default='01')
    op_gravada = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    igv = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    importe = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    descripcion = models.TextField(blank=True)
    estado = models.CharField(max_length=20, default='BORRADOR')
    
    # Campos SUNAT
    xml_firmado = models.TextField(blank=True, null=True)
    sunat_ticket = models.CharField(max_length=100, blank=True, null=True)
    cdr_xml = models.TextField(blank=True, null=True)
    mensaje_sunat = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Nota de Crédito"
        verbose_name_plural = "Notas de Crédito"
        ordering = ['-fecha', '-creado_en']

    def __str__(self):
        return f"NC-{self.serie}-{self.numero:08d}"

    @property
    def nombre_xml(self):
        return f"{self.comprobante_referencia.empresa.ruc}-07-{self.serie}-{self.numero:08d}.xml"

    @property
    def nombre_zip(self):
        return f"{self.comprobante_referencia.empresa.ruc}-07-{self.serie}-{self.numero:08d}.zip"

    def calcular_totales(self):
        from decimal import Decimal
        from django.conf import settings
        tasa_igv = Decimal(str(settings.IGV_TASA))
        op_gravada = Decimal('0.00')
        igv_total = Decimal('0.00')
        importe_total = Decimal('0.00')

        for detalle in self.detalles.all():
            base = detalle.cantidad * detalle.precio_unitario
            if detalle.afecto_igv:
                igv_linea = round(base * tasa_igv, 2)
            else:
                igv_linea = Decimal('0.00')
            subtotal_linea = base + igv_linea

            op_gravada += base
            igv_total += igv_linea
            importe_total += subtotal_linea

        self.op_gravada = op_gravada
        self.igv = igv_total
        self.importe = importe_total
        self.save(update_fields=['op_gravada', 'igv', 'importe'])


class DetalleNotaCredito(ModeloBase):
    nota_credito = models.ForeignKey(
        NotaCredito,
        on_delete=models.CASCADE,
        related_name='detalles'
    )
    producto = models.ForeignKey('productos.Producto', on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=12, decimal_places=4)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=4)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    afecto_igv = models.BooleanField(default=True)
    cod_tipo_afectacion = models.CharField(max_length=10, default='10')
    igv_linea = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Detalle de Nota de Crédito"
        verbose_name_plural = "Detalles de Nota de Crédito"

    def __str__(self):
        return f"{self.nota_credito} - {self.producto.codigo}"
