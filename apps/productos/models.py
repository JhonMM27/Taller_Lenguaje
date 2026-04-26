from django.db import models
from django.core.exceptions import ValidationError


class CategoriaProducto(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    codigo_sunat = models.CharField(max_length=10, blank=True, verbose_name="Código SUNAT")
    activa = models.BooleanField(default=True, verbose_name="Activa")
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Categoría de Producto"
        verbose_name_plural = "Categorías de Productos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    TIPO_OPERACION_CHOICES = [
        ('GRAVADA', 'Operación Gravada'),
        ('EXONERADA', 'Operación Exonerada'),
        ('INAFECTA', 'Operación Inafecta'),
        ('GRATUITA', 'Operación Gratuita'),
        ('EXPORTACION', 'Exportación'),
    ]

    codigo = models.CharField(max_length=30, unique=True, blank=True, null=True, verbose_name="Código")
    descripcion = models.CharField(max_length=500, verbose_name="Descripción")
    unidad_medida = models.CharField(max_length=10, default='NIU', verbose_name="Unidad de Medida")
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Precio Unitario")
    afecto_igv = models.BooleanField(default=True, verbose_name="Afecto IGV")
    cod_tipo_afectacion = models.CharField(max_length=10, default='10', verbose_name="Tipo de Afectación IGV")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    categoria = models.ForeignKey(
        CategoriaProducto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='productos',
        verbose_name="Categoría"
    )
    tipo_operacion = models.CharField(
        max_length=20,
        choices=TIPO_OPERACION_CHOICES,
        default='GRAVADA',
        verbose_name="Tipo de Operación"
    )

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"

    def clean(self):
        if self.precio_unitario < 0:
            raise ValidationError("El precio unitario no puede ser negativo")

    def save(self, *args, **kwargs):
        if not self.codigo:
            last_prod = Producto.objects.order_by('-id').first()
            if last_prod and last_prod.codigo and last_prod.codigo.startswith('PR'):
                try:
                    last_num = int(last_prod.codigo[2:])
                    self.codigo = f"PR{(last_num + 1):04d}"
                except ValueError:
                    self.codigo = "PR0001"
            else:
                self.codigo = "PR0001"
        super().save(*args, **kwargs)