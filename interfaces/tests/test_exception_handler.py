"""
Tests del exception handler.

Verifica que las excepciones de dominio se traducen a HTTP responses
con los codigos correctos.
"""
import pytest
from rest_framework.test import APIRequestFactory

from interfaces.api.exception_handler import domain_exception_handler
from dominio.excepciones import (
    DomainError,
    TipoDocumentoInvalido,
    EstadoInvalido,
    ComprobanteNoAnulable,
    ComprobanteNoAceptado,
    MontoExcedidoError,
    RecursoNoEncontrado,
    ComprobanteNoEncontrado,
    AccesoNoAutorizado,
    ReglaNegocioViolada,
    FirmaDigitalInvalida,
    EnvioSunatFallido,
)


class TestExceptionHandler:
    """Tests del mapeo de excepciones -> HTTP."""

    def setup_method(self):
        self.factory = APIRequestFactory()
        self.context = {"request": self.factory.get("/"), "view": None}

    def test_tipo_documento_invalido_400(self):
        exc = TipoDocumentoInvalido("Factura requiere RUC")
        response = domain_exception_handler(exc, self.context)
        assert response.status_code == 400
        assert "Factura requiere RUC" in str(response.data.get("error", ""))

    def test_estado_invalido_400(self):
        exc = EstadoInvalido("Estado no permitido")
        response = domain_exception_handler(exc, self.context)
        assert response.status_code == 400

    def test_comprobante_no_anulable_422(self):
        exc = ComprobanteNoAnulable("ACEPTADO no se elimina")
        response = domain_exception_handler(exc, self.context)
        assert response.status_code == 422

    def test_comprobante_no_aceptado_422(self):
        exc = ComprobanteNoAceptado("Solo ACEPTADO")
        response = domain_exception_handler(exc, self.context)
        assert response.status_code == 422

    def test_monto_excedido_422(self):
        exc = MontoExcedidoError("Monto excede")
        response = domain_exception_handler(exc, self.context)
        assert response.status_code == 422

    def test_regla_negocio_422(self):
        exc = ReglaNegocioViolada("regla X violada")
        response = domain_exception_handler(exc, self.context)
        assert response.status_code == 422

    def test_recurso_no_encontrado_404(self):
        exc = RecursoNoEncontrado("No existe")
        response = domain_exception_handler(exc, self.context)
        assert response.status_code == 404

    def test_comprobante_no_encontrado_404(self):
        exc = ComprobanteNoEncontrado("Comp X no existe")
        response = domain_exception_handler(exc, self.context)
        assert response.status_code == 404

    def test_acceso_no_autorizado_403(self):
        exc = AccesoNoAutorizado("Sin permisos")
        response = domain_exception_handler(exc, self.context)
        assert response.status_code == 403

    def test_firma_invalida_500(self):
        exc = FirmaDigitalInvalida("Sin firma")
        response = domain_exception_handler(exc, self.context)
        assert response.status_code == 500

    def test_envio_sunat_fallido_502(self):
        exc = EnvioSunatFallido("OSE rechazo")
        response = domain_exception_handler(exc, self.context)
        assert response.status_code == 502

    def test_domain_error_generico_400(self):
        exc = DomainError("error generico")
        response = domain_exception_handler(exc, self.context)
        assert response.status_code == 400

    def test_response_incluye_tipo_y_codigo(self):
        exc = EstadoInvalido("test")
        response = domain_exception_handler(exc, self.context)
        assert "tipo" in response.data
        assert "codigo" in response.data
        assert response.data["tipo"] == "EstadoInvalido"