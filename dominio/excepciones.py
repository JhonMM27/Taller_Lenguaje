"""
Jerarquia de excepciones de dominio.

Esta capa NO importa Django. Es Python puro y puede ser reutilizada
en cualquier contexto (scripts, workers, tests, etc.).
"""

from __future__ import annotations


class DomainError(Exception):
    """Base de todas las excepciones del dominio."""
    pass


class ReglaNegocioViolada(DomainError):
    """Se violo una regla de negocio del dominio."""
    pass


class RecursoNoEncontrado(DomainError):
    """El recurso solicitado no existe o fue eliminado."""
    pass


class AccesoNoAutorizado(DomainError):
    """El usuario no tiene permisos para esta operacion."""
    pass


class TipoDocumentoInvalido(ReglaNegocioViolada):
    """Factura requiere RUC; Boleta requiere DNI/CE/Pasaporte."""
    pass


class EstadoInvalido(ReglaNegocioViolada):
    """Transicion de estado no permitida (ej: ACEPTADO -> BORRADOR)."""
    pass


class ComprobanteNoAnulable(ReglaNegocioViolada):
    """Un comprobante ACEPTADO no se puede eliminar, solo anular via NC."""
    pass


class ComprobanteNoAceptado(ReglaNegocioViolada):
    """Solo se puede emitir NC contra comprobantes ACEPTADOS."""
    pass


class MontoExcedidoError(ReglaNegocioViolada):
    """El monto de la NC excede el total del comprobante original."""
    pass


class SerieNoEncontrada(RecursoNoEncontrado):
    """No existe una serie activa para el tipo y empresa indicados."""
    pass


class CorrelativoConSaltos(ReglaNegocioViolada):
    """Se detecto un salto en la numeracion correlativa."""
    pass


class ComprobanteNoEncontrado(RecursoNoEncontrado):
    """El comprobante solicitado no existe."""
    pass


class ClienteNoEncontrado(RecursoNoEncontrado):
    """El cliente solicitado no existe."""
    pass


class ProductoNoEncontrado(RecursoNoEncontrado):
    """El producto solicitado no existe."""
    pass


class EmpresaNoEncontrada(RecursoNoEncontrado):
    """La empresa emisora no existe."""
    pass


class NotaCreditoNoEncontrada(RecursoNoEncontrado):
    """La nota de credito solicitada no existe."""
    pass


class FirmaDigitalInvalida(ReglaNegocioViolada):
    """El XML no contiene una firma digital valida."""
    pass


class EnvioSunatFallido(DomainError):
    """Error al enviar el comprobante al OSE/SUNAT."""
    pass


class ComprobanteRechazado(EnvioSunatFallido):
    """SUNAT/OSE rechazo el contenido y consumio la numeracion."""
    pass


class ErrorTecnicoEnvio(EnvioSunatFallido):
    """Fallo transitorio sin rechazo tributario ni consumo confirmado."""
    pass


class TicketNoEncontrado(RecursoNoEncontrado):
    """No existe un ticket SUNAT para este comprobante."""
    pass


class DocumentoClienteInvalido(ReglaNegocioViolada):
    """El numero de documento del cliente no es valido."""
    pass


class CertificadoNoDisponible(ReglaNegocioViolada):
    """No hay un certificado digital activo para la empresa."""
    pass
