"""
Modelo de perfil de usuario con roles para el sistema de facturación.
"""

from django.db import models
from django.conf import settings
from apps.core.models import ModeloBase


class PerfilUsuario(ModeloBase):
    """Perfil de usuario con rol asignado."""

    ROL_CHOICES = [
        ('ADMIN', 'Administrador'),
        ('EMISOR', 'Emisor'),
        ('CONTADOR', 'Contador'),
    ]

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil',
    )
    rol = models.CharField(
        max_length=10,
        choices=ROL_CHOICES,
        default='EMISOR',
    )
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios',
        verbose_name='Empresa asignada',
    )

    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'

    def __str__(self):
        return f"{self.usuario.username} - {self.get_rol_display()}"

    @property
    def es_admin(self):
        return self.rol == 'ADMIN'

    @property
    def es_emisor(self):
        return self.rol == 'EMISOR'

    @property
    def es_contador(self):
        return self.rol == 'CONTADOR'
