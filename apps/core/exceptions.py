"""
Backward-compatibility: re-exporta las excepciones de dominio.

Las excepciones originales vivian aqui. Ahora viven en `dominio.excepciones`
(la capa de dominio). Este archivo las re-exporta para mantener
compatibilidad con codigo viejo que las importa desde aqui.
"""
from dominio.excepciones import (
    DomainError as AppError,
    ReglaNegocioViolada,
    RecursoNoEncontrado,
    AccesoNoAutorizado,
    TipoDocumentoInvalido,
    EstadoInvalido,
    ComprobanteNoAnulable,
    SerieNoEncontrada,
    ComprobanteNoEncontrado,
    CorrelativoConSaltos,
    MontoExcedidoError,
    ComprobanteNoAceptado,
    FirmaDigitalInvalida,
    EnvioSunatFallido,
    ComprobanteRechazado,
    ErrorTecnicoEnvio,
    TicketNoEncontrado,
    ClienteNoEncontrado,
    DocumentoClienteInvalido,
    ProductoNoEncontrado,
    EmpresaNoEncontrada,
    NotaCreditoNoEncontrada,
    CertificadoNoDisponible,
)


__all__ = [
    'AppError',
    'ReglaNegocioViolada',
    'RecursoNoEncontrado',
    'AccesoNoAutorizado',
    'TipoDocumentoInvalido',
    'EstadoInvalido',
    'ComprobanteNoAnulable',
    'SerieNoEncontrada',
    'ComprobanteNoEncontrado',
    'CorrelativoConSaltos',
    'MontoExcedidoError',
    'ComprobanteNoAceptado',
    'FirmaDigitalInvalida',
    'EnvioSunatFallido',
    'ComprobanteRechazado',
    'ErrorTecnicoEnvio',
    'TicketNoEncontrado',
    'ClienteNoEncontrado',
    'DocumentoClienteInvalido',
    'ProductoNoEncontrado',
    'EmpresaNoEncontrada',
    'NotaCreditoNoEncontrada',
    'CertificadoNoDisponible',
]
