from django.core.management import call_command
from django.test import TestCase

from apps.productos.models import Producto
from dominio.tributos import AFECTACIONES_IGV


class CrearProductosSunatEjemploTest(TestCase):
    def test_comando_es_idempotente_y_cubre_catalogo_07(self):
        call_command('crear_productos_sunat_ejemplo', verbosity=0)
        call_command('crear_productos_sunat_ejemplo', verbosity=0)

        productos = Producto.objects.filter(codigo__startswith='SUNAT-')
        self.assertEqual(productos.count(), 19)
        self.assertEqual(
            set(productos.values_list('cod_tipo_afectacion', flat=True)),
            set(AFECTACIONES_IGV),
        )
        self.assertTrue(all(producto.precio_unitario == 100 for producto in productos))
