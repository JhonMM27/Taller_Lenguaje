"""
Tests del módulo de Notas de Crédito: validación de monto y estado.
"""

from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.contrib.auth.models import User

from apps.notas_credito.services import NotaCreditoService
from apps.comprobantes.models import Comprobante, SerieComprobante
from apps.empresas.models import Empresa
from apps.clientes.models import Cliente
from apps.productos.models import Producto
from apps.core.exceptions import MontoExcedidoError, ComprobanteNoAceptado


class NotaCreditoServiceTest(TestCase):
    """Tests para NotaCreditoService."""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.empresa = Empresa.objects.create(ruc='20100000001', razon_social='Test SA')
        self.cliente = Cliente.objects.create(
            tipo_doc='6', num_doc='20100000002', razon_social='Cliente SA'
        )
        self.producto = Producto.objects.create(
            descripcion='Producto Test', precio_unitario=Decimal('100.00')
        )
        self.serie = SerieComprobante.objects.create(
            empresa=self.empresa, tipo='01', serie='F001', correlativo_actual=1
        )
        self.comprobante = Comprobante.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            serie=self.serie,
            numero=1,
            fecha=date.today(),
            tipo='01',
            estado='ACEPTADO',
            subtotal=Decimal('100.00'),
            igv=Decimal('18.00'),
            total=Decimal('118.00'),
        )

    def test_nc_contra_comprobante_aceptado(self):
        """NC contra comprobante ACEPTADO debe crearse correctamente."""
        nota = NotaCreditoService.emitir(
            data={
                'comprobante_id': self.comprobante.id,
                'tipo_nc': 'NC',
                'tipo_nota': '01',
                'descripcion': 'Anulación total',
                'monto_afectado': '118.00',
            },
            usuario=self.user,
        )
        self.assertEqual(nota.estado, 'BORRADOR')
        self.assertEqual(nota.comprobante_referencia_id, self.comprobante.id)

    def test_nc_monto_excedido_lanza_error(self):
        """NC con monto mayor al comprobante debe lanzar MontoExcedidoError."""
        with self.assertRaises(MontoExcedidoError):
            NotaCreditoService.emitir(
                data={
                    'comprobante_id': self.comprobante.id,
                    'tipo_nc': 'NC',
                    'tipo_nota': '01',
                    'monto_afectado': '500.00',  # excede 118.00
                },
            )

    def test_nc_contra_comprobante_no_aceptado(self):
        """NC contra comprobante BORRADOR debe lanzar ComprobanteNoAceptado."""
        self.comprobante.estado = 'BORRADOR'
        self.comprobante.save(update_fields=['estado'])

        with self.assertRaises(ComprobanteNoAceptado):
            NotaCreditoService.emitir(
                data={
                    'comprobante_id': self.comprobante.id,
                    'tipo_nc': 'NC',
                    'tipo_nota': '01',
                    'monto_afectado': '50.00',
                },
            )
