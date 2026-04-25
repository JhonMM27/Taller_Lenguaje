from django.db import models
from django.core.exceptions import ValidationError


class Empresa(models.Model):
    ruc = models.CharField(max_length=11, unique=True, verbose_name="RUC")
    razon_social = models.CharField(max_length=200, verbose_name="Razón Social")
    nombre_comercial = models.CharField(max_length=200, blank=True, null=True, verbose_name="Nombre Comercial")
    direccion = models.TextField(blank=True, null=True, verbose_name="Dirección")
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    regimen_tributario = models.CharField(max_length=50, default="GENERAL", verbose_name="Régimen Tributario")
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ['ruc']

    def __str__(self):
        return f"{self.ruc} - {self.razon_social}"

    def clean(self):
        if self.ruc and len(str(self.ruc)) != 11:
            raise ValidationError("El RUC debe tener 11 dígitos")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)