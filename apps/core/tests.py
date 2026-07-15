"""
Tests del módulo core: ModeloBase, soft delete, excepciones.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from apps.core.exceptions import (
    AppError, ReglaNegocioViolada, RecursoNoEncontrado,
    TipoDocumentoInvalido, MontoExcedidoError,
)
from apps.empresas.models import Empresa
from apps.clientes.models import Cliente


class ModeloBaseTest(TestCase):
    """Tests para ModeloBase: auditoría y soft delete."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )

    def test_empresa_tiene_campos_auditoria(self):
        """Verifica que ModeloBase agrega campos de auditoría."""
        empresa = Empresa.objects.create(
            ruc='20100000001',
            razon_social='Test SA',
            creado_por=self.user,
        )
        self.assertIsNotNone(empresa.creado_en)
        self.assertIsNotNone(empresa.actualizado_en)
        self.assertEqual(empresa.creado_por, self.user)
        self.assertTrue(empresa.activo)

    def test_soft_delete_marca_inactivo(self):
        """Verifica que eliminar() hace soft delete (no borra físicamente)."""
        empresa = Empresa.objects.create(
            ruc='20100000002',
            razon_social='Empresa para eliminar',
        )
        empresa_id = empresa.id

        empresa.eliminar(usuario=self.user)

        # Sigue existiendo en BD
        empresa_db = Empresa.objects.get(pk=empresa_id)
        self.assertFalse(empresa_db.activo)

    def test_manager_activos_filtra_inactivos(self):
        """Verifica que el manager 'activos' solo retorna registros activos."""
        Empresa.objects.create(ruc='20100000003', razon_social='Activa SA')
        emp_inactiva = Empresa.objects.create(ruc='20100000004', razon_social='Inactiva SA')
        emp_inactiva.eliminar()

        activas = Empresa.activos.all()
        self.assertEqual(activas.count(), 1)
        self.assertEqual(activas.first().razon_social, 'Activa SA')

        # objects retorna todas
        todas = Empresa.objects.all()
        self.assertEqual(todas.count(), 2)


class ExcepcionesTest(TestCase):
    """Tests para la jerarquía de excepciones de dominio."""

    def test_excepciones_heredan_de_app_error(self):
        """Verifica que todas las excepciones heredan de AppError."""
        self.assertTrue(issubclass(ReglaNegocioViolada, AppError))
        self.assertTrue(issubclass(RecursoNoEncontrado, AppError))
        self.assertTrue(issubclass(TipoDocumentoInvalido, ReglaNegocioViolada))
        self.assertTrue(issubclass(MontoExcedidoError, ReglaNegocioViolada))

    def test_excepcion_con_mensaje(self):
        """Verifica que las excepciones de dominio pueden llevar mensaje."""
        exc = TipoDocumentoInvalido("Factura requiere RUC")
        self.assertEqual(str(exc), "Factura requiere RUC")

    def test_captura_por_base(self):
        """Verifica que se puede capturar por la clase base."""
        with self.assertRaises(AppError):
            raise TipoDocumentoInvalido("Test")
