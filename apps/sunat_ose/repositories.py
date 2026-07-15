"""
Repository Pattern para el módulo SUNAT/OSE.

Abstrae el acceso al log de envíos SUNAT.
Facilita mock en tests y desacopla la persistencia.
"""

from typing import Protocol, Optional
from django.db.models import QuerySet

from apps.comprobantes.models import Comprobante, LogEnvioSUNAT
from apps.core.exceptions import RecursoNoEncontrado


# ──────────────────────────────────────────────────────────────
# Puerto (Interface)
# ──────────────────────────────────────────────────────────────

class ILogSunatRepository(Protocol):
    """Interface para el repositorio de logs de SUNAT."""

    def registrar_envio(
        self,
        comprobante: Comprobante,
        estado_respuesta: str,
        codigo_respuesta: str,
        descripcion: str,
        uuid: str = '',
        cdr_xml: str = '',
    ) -> LogEnvioSUNAT:
        """Registra un log de envío a SUNAT."""
        ...

    def obtener_por_comprobante(self, comprobante_id: int) -> QuerySet:
        """Obtiene todos los logs de un comprobante."""
        ...

    def obtener_cdr(self, comprobante_id: int) -> Optional[LogEnvioSUNAT]:
        """Obtiene el CDR más reciente de un comprobante."""
        ...


# ──────────────────────────────────────────────────────────────
# Adaptador (Implementación Django ORM)
# ──────────────────────────────────────────────────────────────

class LogSunatRepositoryDjango:
    """Implementación del repositorio de logs SUNAT usando Django ORM."""

    def registrar_envio(
        self,
        comprobante: Comprobante,
        estado_respuesta: str,
        codigo_respuesta: str,
        descripcion: str,
        uuid: str = '',
        cdr_xml: str = '',
    ) -> LogEnvioSUNAT:
        return LogEnvioSUNAT.objects.create(
            comprobante=comprobante,
            estado_respuesta=estado_respuesta,
            codigo_respuesta=codigo_respuesta,
            descripcion=descripcion,
            uuid=uuid,
            cdr_xml=cdr_xml,
        )

    def obtener_por_comprobante(self, comprobante_id: int) -> QuerySet:
        return LogEnvioSUNAT.objects.filter(
            comprobante_id=comprobante_id
        ).order_by('-fecha_envio')

    def obtener_cdr(self, comprobante_id: int) -> Optional[LogEnvioSUNAT]:
        return LogEnvioSUNAT.objects.filter(
            comprobante_id=comprobante_id,
            cdr_xml__isnull=False,
        ).exclude(cdr_xml='').first()
