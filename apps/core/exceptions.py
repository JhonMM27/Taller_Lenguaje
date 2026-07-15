"""
Jerarquía de excepciones de dominio del sistema de Facturación Electrónica.

Nunca lanzar ValueError, Exception u otros genéricos.
Todas las excepciones del sistema heredan de AppError.
"""


# ──────────────────────────────────────────────────────────────
# Base
# ──────────────────────────────────────────────────────────────

class AppError(Exception):
    """Base de todas las excepciones de la aplicación."""
    pass


# ──────────────────────────────────────────────────────────────
# Categorías generales
# ──────────────────────────────────────────────────────────────

class ReglaNegocioViolada(AppError):
    """Se violó una regla de negocio del dominio."""
    pass


class RecursoNoEncontrado(AppError):
    """El recurso solicitado no existe o fue eliminado."""
    pass


class AccesoNoAutorizado(AppError):
    """El usuario no tiene permisos para esta operación."""
    pass


# ──────────────────────────────────────────────────────────────
# Excepciones de Comprobantes
# ──────────────────────────────────────────────────────────────

class TipoDocumentoInvalido(ReglaNegocioViolada):
    """Factura requiere RUC; Boleta requiere DNI."""
    pass


class EstadoInvalido(ReglaNegocioViolada):
    """Transición de estado no permitida (ej: ACEPTADO → BORRADOR)."""
    pass


class ComprobanteNoAnulable(ReglaNegocioViolada):
    """Un comprobante ACEPTADO no se puede eliminar, solo anular vía NC."""
    pass


class SerieNoEncontrada(RecursoNoEncontrado):
    """No existe una serie activa para el tipo y empresa indicados."""
    pass


class ComprobanteNoEncontrado(RecursoNoEncontrado):
    """El comprobante solicitado no existe."""
    pass


class CorrelativoConSaltos(ReglaNegocioViolada):
    """Se detectó un salto en la numeración correlativa."""
    pass


# ──────────────────────────────────────────────────────────────
# Excepciones de Notas de Crédito
# ──────────────────────────────────────────────────────────────

class MontoExcedidoError(ReglaNegocioViolada):
    """El monto de la NC excede el total del comprobante original."""
    pass


class ComprobanteNoAceptado(ReglaNegocioViolada):
    """Solo se puede emitir NC contra comprobantes ACEPTADOS."""
    pass


# ──────────────────────────────────────────────────────────────
# Excepciones de SUNAT / OSE
# ──────────────────────────────────────────────────────────────

class FirmaDigitalInvalida(ReglaNegocioViolada):
    """El XML no contiene una firma digital válida."""
    pass


class EnvioSunatFallido(AppError):
    """Error al enviar el comprobante al OSE/SUNAT."""
    pass


class TicketNoEncontrado(RecursoNoEncontrado):
    """No existe un ticket SUNAT para este comprobante."""
    pass


# ──────────────────────────────────────────────────────────────
# Excepciones de Clientes
# ──────────────────────────────────────────────────────────────

class ClienteNoEncontrado(RecursoNoEncontrado):
    """El cliente solicitado no existe."""
    pass


class DocumentoClienteInvalido(ReglaNegocioViolada):
    """El número de documento del cliente no es válido."""
    pass


# ──────────────────────────────────────────────────────────────
# Excepciones de Productos
# ──────────────────────────────────────────────────────────────

class ProductoNoEncontrado(RecursoNoEncontrado):
    """El producto solicitado no existe."""
    pass


# ──────────────────────────────────────────────────────────────
# Excepciones de Empresa / Certificados
# ──────────────────────────────────────────────────────────────

class EmpresaNoEncontrada(RecursoNoEncontrado):
    """No existe la empresa emisora."""
    pass


class CertificadoNoDisponible(ReglaNegocioViolada):
    """No hay un certificado digital activo para la empresa."""
    pass
