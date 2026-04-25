from django.db import models
from django.core.exceptions import ValidationError
from apps.comprobantes.models import Comprobante


class NotaCredito(models.Model):
    MOTIVO_CHOICES = [
        ('01', 'Anulación de la operación'),
        ('02', 'Anulación por error en el RUC'),
        ('03', 'Corrección por error en la descripción'),
        ('04', 'Descuento global'),
        ('05', 'Descuento por ítem'),
        ('06', 'Devolución por ítem'),
        ('07', 'Devolución total'),
        ('08', 'Bonificación'),
        ('09', 'Disminución del valor'),
        ('10', 'Otros'),
    ]

    comprobante_referencia = models.ForeignKey(
        Comprobante,
        on_delete=models.PROTECT,
        related_name='notas_credito'
    )
    serie = models.CharField(max_length=4)
    numero = models.PositiveIntegerField()
    fecha = models.DateField()
    tipo_nota = models.CharField(max_length=2, choices=MOTIVO_CHOICES)
    monto_afectado = models.DecimalField(max_digits=14, decimal_places=2)
    descripcion = models.TextField(blank=True)
    estado = models.CharField(max_length=20, default='BORRADOR')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Nota de Crédito"
        verbose_name_plural = "Notas de Crédito"
        ordering = ['-fecha', '-created_at']

    def __str__(self):
        return f"NC-{self.serie}-{self.numero:08d}"

    def clean(self):
        if self.monto_afectado > self.comprobante_referencia.total:
            raise ValidationError("El monto afectado no puede exceder el total del comprobante original")