"""
Backward-compatibility: shim que re-exporta el repositorio de log legacy.

El servicio legacy `SunatEnvioService` usa este repositorio para registrar
logs de envios a SUNAT.
"""
from decimal import Decimal
from typing import Optional


class LogSunatRepositoryDjango:
    """Wrapper legacy que persiste logs usando Django ORM directamente."""

    def registrar_envio(
        self,
        comprobante,
        estado_respuesta: str,
        codigo_respuesta: str,
        descripcion: str,
        uuid: str = '',
        cdr_xml: str = '',
    ):
        from apps.comprobantes.models import LogEnvioSUNAT
        LogEnvioSUNAT.objects.create(
            comprobante_id=comprobante.id,
            estado_respuesta=estado_respuesta,
            codigo_respuesta=codigo_respuesta,
            descripcion=descripcion,
            uuid=uuid or None,
            cdr_xml=cdr_xml or None,
        )

    def obtener_por_comprobante(self, comprobante_id: int):
        from apps.comprobantes.models import LogEnvioSUNAT
        return list(LogEnvioSUNAT.objects.filter(
            comprobante_id=comprobante_id
        ).order_by("-fecha_envio"))


__all__ = ["LogSunatRepositoryDjango"]
