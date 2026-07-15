"""
Tests de los endpoints de la API.

Usa APIClient de DRF para hacer requests HTTP simulados.
"""
import pytest
from rest_framework.test import APIClient
from decimal import Decimal
from datetime import date


@pytest.fixture
def cliente_ruc(db):
    from apps.clientes.models import Cliente
    return Cliente.objects.create(
        tipo_doc="6", num_doc="20999999991", razon_social="RUC SA",
    )


@pytest.fixture
def cliente_dni(db):
    from apps.clientes.models import Cliente
    return Cliente.objects.create(
        tipo_doc="1", num_doc="12345678", razon_social="DNI SA",
    )


@pytest.fixture
def empresa(db):
    from apps.empresas.models import Empresa
    return Empresa.objects.create(
        ruc="20999999999", razon_social="EMPRESA SA",
    )


@pytest.fixture
def producto(db):
    from apps.productos.models import Producto
    return Producto.objects.create(
        descripcion="Prod Test", precio_unitario=Decimal("100"),
    )


@pytest.fixture
def admin_user(db):
    from django.contrib.auth.models import User
    from apps.usuarios.models import PerfilUsuario
    user = User.objects.create_user(
        username="admin_test", password="admin123",
    )
    PerfilUsuario.objects.create(usuario=user, rol="ADMIN")
    return user


@pytest.mark.django_db
class TestHealthView:
    def test_health_check(self):
        client = APIClient()
        response = client.get("/api/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "database" in data
        assert "sunat_mock" in data


@pytest.mark.django_db
class TestClienteAPI:
    def test_listar_clientes(self, admin_user):
        client = APIClient()
        client.force_authenticate(user=admin_user)
        response = client.get("/api/clientes/")
        assert response.status_code == 200

    def test_crear_cliente_ruc(self, admin_user):
        client = APIClient()
        client.force_authenticate(user=admin_user)
        response = client.post("/api/clientes/", {
            "tipo_doc": "6",
            "num_doc": "20111111111",
            "razon_social": "Nueva SA",
        }, format="json")
        assert response.status_code == 201
        data = response.json()
        # El serializer retorna modelo Django, con campos snake_case
        assert data["num_doc"] == "20111111111"


@pytest.mark.django_db
class TestProductoAPI:
    def test_listar_productos(self, admin_user):
        client = APIClient()
        client.force_authenticate(user=admin_user)
        response = client.get("/api/productos/")
        assert response.status_code == 200

    def test_crear_producto(self, admin_user):
        client = APIClient()
        client.force_authenticate(user=admin_user)
        response = client.post("/api/productos/", {
            "descripcion": "Test Prod",
            "precio_unitario": "50.00",
        }, format="json")
        assert response.status_code == 201


@pytest.mark.django_db
class TestComprobanteAPI:
    def test_crear_factura_con_ruc(self, admin_user, empresa, cliente_ruc, producto):
        client = APIClient()
        client.force_authenticate(user=admin_user)
        response = client.post("/api/comprobantes/", {
            "empresa_id": empresa.id,
            "cliente_id": cliente_ruc.id,
            "fecha": str(date.today()),
            "tipo": "01",
            "detalles": [
                {"producto_id": producto.id, "cantidad": "2"}
            ],
        }, format="json")
        assert response.status_code == 201
        data = response.json()
        assert data["tipo"] == "01"

    def test_crear_factura_con_dni_retorna_400(self, admin_user, empresa, cliente_dni, producto):
        client = APIClient()
        client.force_authenticate(user=admin_user)
        response = client.post("/api/comprobantes/", {
            "empresa_id": empresa.id,
            "cliente_id": cliente_dni.id,
            "fecha": str(date.today()),
            "tipo": "01",
            "detalles": [
                {"producto_id": producto.id, "cantidad": "1"}
            ],
        }, format="json")
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "RUC" in data["error"]

    def test_listar_comprobantes(self, admin_user, empresa, cliente_ruc, producto):
        # Primero crear
        client = APIClient()
        client.force_authenticate(user=admin_user)
        client.post("/api/comprobantes/", {
            "empresa_id": empresa.id,
            "cliente_id": cliente_ruc.id,
            "fecha": str(date.today()),
            "tipo": "01",
            "detalles": [
                {"producto_id": producto.id, "cantidad": "1"}
            ],
        }, format="json")
        # Listar
        response = client.get("/api/comprobantes/")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "count" in data


@pytest.mark.django_db
class TestAuthJWT:
    def test_obtener_token(self, db):
        from django.contrib.auth.models import User
        User.objects.create_user(username="jwtuser", password="jwtpass123")
        client = APIClient()
        response = client.post("/api/auth/token/", {
            "username": "jwtuser",
            "password": "jwtpass123",
        }, format="json")
        assert response.status_code == 200
        data = response.json()
        assert "access" in data
        assert "refresh" in data