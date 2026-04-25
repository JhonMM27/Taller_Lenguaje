from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError


class Cliente(models.Model):
    TIPO_DOC_CHOICES = [
        ('1', 'DNI'),
        ('6', 'RUC'),
        ('4', 'Carnet de Extranjería'),
        ('7', 'Pasaporte'),
        ('A', 'Cédula de Identidad'),
    ]

    tipo_doc = models.CharField(max_length=2, choices=TIPO_DOC_CHOICES, default='6')
    num_doc = models.CharField(max_length=15, validators=[RegexValidator(r'^\d+$')])
    razon_social = models.CharField(max_length=200, verbose_name="Razón Social/Nombre")
    direccion = models.TextField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    ubigeo = models.CharField(max_length=6, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['razon_social']
        unique_together = ['tipo_doc', 'num_doc']

    def __str__(self):
        return f"{self.get_tipo_doc_display()} {self.num_doc} - {self.razon_social}"

    def clean(self):
        num_doc_str = str(self.num_doc) if self.num_doc else ''
        if self.tipo_doc == '6' and num_doc_str and len(num_doc_str) != 11:
            raise ValidationError("El RUC debe tener 11 dígitos")
        if self.tipo_doc == '1' and num_doc_str and len(num_doc_str) != 8:
            raise ValidationError("El DNI debe tener 8 dígitos")