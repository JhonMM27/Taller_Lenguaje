from django.db import models
from apps.core.models import ModeloBase
from apps.empresas.models import Empresa


class LoteEnvio(ModeloBase):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='lotes_envio')
    fecha_emision_documentos = models.DateField()
    total_documentos = models.PositiveIntegerField(default=0)
    enviandos = models.PositiveIntegerField(default=0)
    aceptados = models.PositiveIntegerField(default=0)
    rechazados = models.PositiveIntegerField(default=0)
    estado = models.CharField(
        max_length=20,
        choices=[
            ('PENDIENTE', 'Pendiente'),
            ('PROCESANDO', 'Procesando'),
            ('COMPLETADO', 'Completado'),
            ('ERROR', 'Error'),
        ],
        default='PENDIENTE'
    )
    ticket_ose = models.CharField(max_length=100, blank=True, null=True)
    observacion = models.TextField(blank=True)

    class Meta:
        verbose_name = "Lote de Envío"
        verbose_name_plural = "Lotes de Envío"
        ordering = ['-creado_en']

    def __str__(self):
        return f"Lote {self.id} - {self.creado_en.strftime('%Y-%m-%d %H:%M')} - {self.estado}"