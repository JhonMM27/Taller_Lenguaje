from django.db import models
from django.core.exceptions import ValidationError


class Producto(models.Model):
    codigo = models.CharField(max_length=30, unique=True, verbose_name="Código")
    descripcion = models.CharField(max_length=500, verbose_name="Descripción")
    unidad_medida = models.CharField(max_length=10, default='NIU', verbose_name="Unidad de Medida")
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Precio Unitario")
    afecto_igv = models.BooleanField(default=True, verbose_name="Afecto IGV")
    cod_tipo_afectacion = models.CharField(max_length=10, default='10', verbose_name="Tipo de Afectación IGV")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"

    def clean(self):
        if self.precio_unitario < 0:
            raise ValidationError("El precio unitario no puede ser negativo")