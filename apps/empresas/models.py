from django.db import models
from django.core.exceptions import ValidationError


class Empresa(models.Model):
    ruc = models.CharField(max_length=11, unique=True, verbose_name="RUC")
    codigo = models.CharField(max_length=10, unique=True, blank=True, null=True, verbose_name="Código")
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
        if self.ruc and len(str(self.ruc)) != 10:
            raise ValidationError("El RUC debe tener 10 dígitos")
        if self.telefono and len(str(self.telefono).strip()) != 9:
            raise ValidationError("El teléfono debe tener exactamente 9 dígitos")

    def save(self, *args, **kwargs):
        if not self.codigo:
            last_emp = Empresa.objects.order_by('-id').first()
            if last_emp and last_emp.codigo and last_emp.codigo.startswith('EM'):
                try:
                    last_num = int(last_emp.codigo[2:])
                    self.codigo = f"EM{(last_num + 1):04d}"
                except ValueError:
                    self.codigo = "EM0001"
            else:
                self.codigo = "EM0001"
        self.full_clean()
        super().save(*args, **kwargs)