"""
DRF custom exception handler que traduce excepciones de dominio
a HTTP responses con los codigos correctos.

Mapeo:
    - TipoDocumentoInvalido    -> 400
    - EstadoInvalido           -> 400
    - ComprobanteNoAnulable    -> 422
    - ComprobanteNoAceptado    -> 422
    - MontoExcedidoError       -> 422
    - RecursoNoEncontrado      -> 404
    - AccesoNoAutorizado       -> 403
    - ReglaNegocioViolada      -> 422
    - FirmaDigitalInvalida     -> 500
    - EnvioSunatFallido        -> 502
    - DomainError              -> 400
"""
from __future__ import annotations

import logging
from rest_framework.views import exception_handler as drf_default_handler
from rest_framework.response import Response
from rest_framework import status as drf_status

from dominio.excepciones import (
    AccesoNoAutorizado,
    ClienteNoEncontrado,
    ComprobanteNoAceptado,
    ComprobanteNoAnulable,
    ComprobanteNoEncontrado,
    DomainError,
    EmpresaNoEncontrada,
    EnvioSunatFallido,
    EstadoInvalido,
    FirmaDigitalInvalida,
    MontoExcedidoError,
    NotaCreditoNoEncontrada,
    ProductoNoEncontrado,
    RecursoNoEncontrado,
    ReglaNegocioViolada,
    SerieNoEncontrada,
    TicketNoEncontrado,
    TipoDocumentoInvalido,
)

logger = logging.getLogger(__name__)


MAPA_EXCEPCIONES = {
    # Clases mas especificas primero
    TipoDocumentoInvalido: drf_status.HTTP_400_BAD_REQUEST,
    EstadoInvalido: drf_status.HTTP_400_BAD_REQUEST,
    MontoExcedidoError: drf_status.HTTP_422_UNPROCESSABLE_ENTITY,
    ComprobanteNoAnulable: drf_status.HTTP_422_UNPROCESSABLE_ENTITY,
    ComprobanteNoAceptado: drf_status.HTTP_422_UNPROCESSABLE_ENTITY,
    ComprobanteNoEncontrado: drf_status.HTTP_404_NOT_FOUND,
    ClienteNoEncontrado: drf_status.HTTP_404_NOT_FOUND,
    ProductoNoEncontrado: drf_status.HTTP_404_NOT_FOUND,
    EmpresaNoEncontrada: drf_status.HTTP_404_NOT_FOUND,
    NotaCreditoNoEncontrada: drf_status.HTTP_404_NOT_FOUND,
    SerieNoEncontrada: drf_status.HTTP_404_NOT_FOUND,
    TicketNoEncontrado: drf_status.HTTP_404_NOT_FOUND,
    EnvioSunatFallido: drf_status.HTTP_502_BAD_GATEWAY,
    FirmaDigitalInvalida: drf_status.HTTP_500_INTERNAL_SERVER_ERROR,
    AccesoNoAutorizado: drf_status.HTTP_403_FORBIDDEN,
    # Clases mas generales al final
    RecursoNoEncontrado: drf_status.HTTP_404_NOT_FOUND,
    ReglaNegocioViolada: drf_status.HTTP_422_UNPROCESSABLE_ENTITY,
    DomainError: drf_status.HTTP_400_BAD_REQUEST,
}


def domain_exception_handler(exc, context):
    """Manejador de excepciones que traduce DomainError -> Response."""
    if isinstance(exc, DomainError):
        # Buscar la clase mas especifica en el mapa
        http_status = drf_status.HTTP_400_BAD_REQUEST
        for cls, status_code in MAPA_EXCEPCIONES.items():
            if isinstance(exc, cls):
                http_status = status_code
                break
        tipo = type(exc).__name__
        logger.info(
            "Excepcion de dominio capturada: %s - %s (HTTP %s)",
            tipo, exc, http_status,
        )
        return Response(
            {
                "error": str(exc),
                "tipo": tipo,
                "codigo": tipo.upper(),
            },
            status=http_status,
        )
    # Si no es de dominio, usar el handler por defecto de DRF.
    return drf_default_handler(exc, context)