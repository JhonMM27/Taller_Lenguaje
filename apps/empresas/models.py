from django.db import models
from django.core.exceptions import ValidationError


class Certificado(models.Model):
    empresa = models.ForeignKey(
        'Empresa',
        on_delete=models.CASCADE,
        related_name='certificados'
    )
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    certificado_binario = models.BinaryField(verbose_name="Certificado (.pfx)")
    contrasena = models.BinaryField(verbose_name="Contrasena (cifrada)")
    numero_serie = models.CharField(max_length=100, verbose_name="Numero de Serie")
    fecha_desde = models.DateField(verbose_name="Valido desde")
    fecha_hasta = models.DateField(verbose_name="Valido hasta")
    huella_digital = models.CharField(max_length=64, verbose_name="Huella Digital (SHA256)")
    is_active = models.BooleanField(default=False, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Certificado"
        verbose_name_plural = "Certificados"
        ordering = ['-is_active', '-fecha_hasta']
        constraints = [
            models.UniqueConstraint(
                fields=['empresa'],
                condition=models.Q(is_active=True),
                name='unique_active_cert_per_empresa'
            )
        ]

    def __str__(self):
        estado = "ACTIVO" if self.is_active else "VENCIDO"
        return f"{self.nombre} ({estado}) - {self.empresa.ruc}"

    def save(self, *args, **kwargs):
        if self.is_active:
            Certificado.objects.filter(empresa=self.empresa, is_active=True).update(is_active=False)
        super().save(*args, **kwargs)


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

    @property
    def certificado_activo(self):
        return self.certificados.filter(is_active=True).first()

    def clean(self):
        if self.ruc and len(str(self.ruc)) != 11:
            raise ValidationError("El RUC debe tener 11 dígitos")
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