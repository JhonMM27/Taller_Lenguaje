"""
Fixtures compartidos para todos los tests del proyecto.

Provee factories y objetos de uso frecuente para evitar duplicación.
"""
import pytest
from decimal import Decimal
from datetime import date


@pytest.fixture
def empresa_factory(db):
    """Factory para crear empresas en tests."""
    from apps.empresas.models import Empresa

    def _create(ruc='20100000001', razon_social='Empresa Test SA'):
        return Empresa.objects.create(ruc=ruc, razon_social=razon_social)

    return _create


@pytest.fixture
def cliente_factory(db):
    """Factory para crear clientes en tests."""
    from apps.clientes.models import Cliente

    def _create(tipo_doc='6', num_doc='20100000002', razon_social='Cliente Test SA'):
        return Cliente.objects.create(
            tipo_doc=tipo_doc,
            num_doc=num_doc,
            razon_social=razon_social,
        )

    return _create


@pytest.fixture
def producto_factory(db):
    """Factory para crear productos en tests."""
    from apps.productos.models import Producto

    def _create(descripcion='Producto Test', precio='100.00', afecto_igv=True):
        return Producto.objects.create(
            descripcion=descripcion,
            precio_unitario=Decimal(str(precio)),
            afecto_igv=afecto_igv,
        )

    return _create


@pytest.fixture
def empresa(empresa_factory):
    return empresa_factory()


@pytest.fixture
def cliente_ruc(cliente_factory):
    return cliente_factory(tipo_doc='6', num_doc='20100000002')


@pytest.fixture
def cliente_dni(cliente_factory):
    return cliente_factory(tipo_doc='1', num_doc='12345678')


@pytest.fixture
def producto(producto_factory):
    return producto_factory()


@pytest.fixture
def admin_user(db):
    """Usuario administrador con perfil ADMIN."""
    from django.contrib.auth.models import User
    from apps.usuarios.models import PerfilUsuario

    user = User.objects.create_user(
        username='admin_test',
        password='adminpass123',
        email='admin@test.com',
    )
    user.is_staff = True
    user.is_superuser = True
    user.save()
    PerfilUsuario.objects.create(usuario=user, rol='ADMIN')
    return user


@pytest.fixture
def emisor_user(db, empresa):
    """Usuario emisor con perfil EMISOR asignado a una empresa."""
    from django.contrib.auth.models import User
    from apps.usuarios.models import PerfilUsuario

    user = User.objects.create_user(
        username='emisor_test',
        password='emisorpass123',
        email='emisor@test.com',
    )
    PerfilUsuario.objects.create(usuario=user, rol='EMISOR', empresa=empresa)
    return user


@pytest.fixture
def contador_user(db, empresa):
    """Usuario contador con perfil CONTADOR asignado a una empresa."""
    from django.contrib.auth.models import User
    from apps.usuarios.models import PerfilUsuario

    user = User.objects.create_user(
        username='contador_test',
        password='contadorpass123',
        email='contador@test.com',
    )
    PerfilUsuario.objects.create(usuario=user, rol='CONTADOR', empresa=empresa)
    return user


@pytest.fixture
def fecha_hoy():
    """Fecha de hoy en formato string."""
    return str(date.today())


@pytest.fixture
def comprobante_aceptado(empresa, cliente_ruc, producto):
    """Crea un comprobante en estado ACEPTADO listo para tests."""
    from apps.comprobantes.services import ComprobanteService
    from apps.comprobantes.models import Comprobante

    comp = ComprobanteService.crear(
        data={
            'empresa_id': empresa.id,
            'cliente_id': cliente_ruc.id,
            'fecha': str(date.today()),
            'tipo': '01',
            'detalles': [
                {'producto_id': producto.id, 'cantidad': 2, 'precio_unitario': '100.00'}
            ],
        },
    )
    comp.estado = 'ACEPTADO'
    comp.subtotal = Decimal('200.00')
    comp.igv = Decimal('36.00')
    comp.total = Decimal('236.00')
    comp.save()
    return comp