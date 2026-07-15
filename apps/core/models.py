"""
Modelo base abstracto con auditoría y soft delete.

Todos los modelos del sistema DEBEN heredar de ModeloBase.
Proporciona:
  - creado_en (auto_now_add)
  - actualizado_en (auto_now)
  - creado_por (FK a User, nullable)
  - activo (bool, default=True)
  - Manager 'activos' para filtrar solo registros activos
  - Método eliminar() para soft delete
"""

from django.db import models
from django.conf import settings


class ManagerActivos(models.Manager):
    """Manager que retorna solo registros activos (soft delete)."""

    def get_queryset(self):
        return super().get_queryset().filter(activo=True)


class ModeloBase(models.Model):
    """
    Modelo base abstracto del sistema.
    Todos los modelos heredan de aquí para tener auditoría y soft delete.
    """
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name='+',
        on_delete=models.SET_NULL,
    )
    activo = models.BooleanField(default=True, db_index=True)

    # Managers
    objects = models.Manager()      # todos los registros
    activos = ManagerActivos()      # solo activos

    def eliminar(self, usuario=None):
        """Soft delete: marca como inactivo, nunca borrar físicamente."""
        self.activo = False
        update_fields = ['activo', 'actualizado_en']
        if usuario:
            self.creado_por = usuario
            update_fields.append('creado_por')
        self.save(update_fields=update_fields)

    class Meta:
        abstract = True
