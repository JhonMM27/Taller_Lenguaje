from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import ModeloBase


class Cliente(ModeloBase):
    TIPO_DOC_CHOICES = [
        ('0', 'Doc. tributario no domiciliado sin RUC'),
        ('1', 'DNI'),
        ('6', 'RUC'),
        ('4', 'Carnet de Extranjería'),
        ('7', 'Pasaporte'),
        ('A', 'Cédula de Identidad'),
    ]

    tipo_doc = models.CharField(max_length=2, choices=TIPO_DOC_CHOICES, default='6')
    codigo = models.CharField(max_length=10, unique=True, blank=True, null=True, verbose_name="Código")
    num_doc = models.CharField(max_length=15)
    razon_social = models.CharField(max_length=200, verbose_name="Razón Social/Nombre")
    direccion = models.TextField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    ubigeo = models.CharField(max_length=6, blank=True, null=True)
    pais_codigo = models.CharField(
        max_length=2, default='PE', verbose_name='País de residencia (ISO-3166)'
    )

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['razon_social']
        unique_together = ['tipo_doc', 'num_doc']

    def __str__(self):
        return f"{self.get_tipo_doc_display()} {self.num_doc} - {self.razon_social}"

    def save(self, *args, **kwargs):
        if not self.codigo:
            last_cliente = Cliente.objects.order_by('-id').first()
            if last_cliente and last_cliente.codigo and last_cliente.codigo.startswith('CL'):
                try:
                    last_num = int(last_cliente.codigo[2:])
                    self.codigo = f"CL{(last_num + 1):04d}"
                except ValueError:
                    self.codigo = "CL0001"
            else:
                self.codigo = "CL0001"
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        num_doc_str = str(self.num_doc).strip() if self.num_doc else ''
        errors = {}
        if self.tipo_doc == '6' and (
            not num_doc_str.isdigit() or len(num_doc_str) != 11
        ):
            errors['num_doc'] = "El RUC debe tener exactamente 11 dígitos"
        elif self.tipo_doc == '1' and (
            not num_doc_str.isdigit() or len(num_doc_str) != 8
        ):
            errors['num_doc'] = "El DNI debe tener exactamente 8 dígitos"
        elif self.tipo_doc in ('0', '4', '7', 'A') and (
            not num_doc_str or len(num_doc_str) > 15
            or any(caracter.isspace() for caracter in num_doc_str)
        ):
            errors['num_doc'] = (
                "El documento extranjero debe tener hasta 15 caracteres y no contener espacios"
            )

        pais = str(self.pais_codigo or '').strip().upper()
        if len(pais) != 2 or not pais.isalpha():
            errors['pais_codigo'] = "Use un código de país ISO-3166 de dos letras"
        else:
            self.pais_codigo = pais
        
        if self.telefono and len(str(self.telefono).strip()) != 9:
            errors['telefono'] = "El teléfono debe tener exactamente 9 dígitos"
            
        if errors:
            raise ValidationError(errors)
