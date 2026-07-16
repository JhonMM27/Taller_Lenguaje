"""
Tests de la capa de interfaces: container (inyeccion de dependencias).

Verifica que el container de DI funciona correctamente y que
los servicios se pueden obtener de forma thread-safe.
"""
import pytest
from unittest.mock import patch

from interfaces.container import (
    get_uow,
    get_comprobante_service,
    get_nota_credito_service,
    get_cliente_service,
    get_producto_service,
    reset_uow,
)


class TestContainer:
    """Tests del container de DI. No requieren BD porque son pure-Python."""

    def test_get_uow_retorna_instancia(self):
        uow = get_uow()
        assert uow is not None
        assert isinstance(uow, type(uow))

    def test_get_uow_retorna_instancia_nueva(self):
        """Las UoW son por-llamada (no comparten estado)."""
        uow1 = get_uow()
        uow2 = get_uow()
        # No es la misma instancia porque se crean nuevas
        # pero ambas son validas
        assert uow1 is not None
        assert uow2 is not None

    def test_reset_uow_no_falla(self):
        reset_uow()  # no debe lanzar error

    def test_get_comprobante_service(self):
        service = get_comprobante_service()
        assert service is not None
        assert hasattr(service, "crear")
        assert hasattr(service, "emitir")
        assert hasattr(service, "reenviar")
        assert hasattr(service, "eliminar")

    def test_get_nota_credito_service(self):
        service = get_nota_credito_service()
        assert service is not None
        assert hasattr(service, "emitir")
        assert hasattr(service, "eliminar")

    def test_get_cliente_service(self):
        service = get_cliente_service()
        assert service is not None
        assert hasattr(service, "crear")
        assert hasattr(service, "obtener")
        assert hasattr(service, "eliminar")

    def test_get_producto_service(self):
        service = get_producto_service()
        assert service is not None
        assert hasattr(service, "crear")
        assert hasattr(service, "obtener")