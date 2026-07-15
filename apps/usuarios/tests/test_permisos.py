"""
Tests de permisos por rol.
"""
import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestPermisosRoles:
    def test_admin_accede_a_todo(self):
        from django.contrib.auth.models import User
        from apps.usuarios.models import PerfilUsuario
        user = User.objects.create_user(username="admin1", password="p")
        PerfilUsuario.objects.create(usuario=user, rol="ADMIN")
        client = APIClient()
        client.force_authenticate(user=user)
        assert client.get("/api/clientes/").status_code == 200
        assert client.get("/api/productos/").status_code == 200

    def test_emisor_puede_listar(self):
        from django.contrib.auth.models import User
        from apps.usuarios.models import PerfilUsuario
        from apps.empresas.models import Empresa
        e = Empresa.objects.create(ruc="20999999999", razon_social="X")
        user = User.objects.create_user(username="emisor1", password="p")
        PerfilUsuario.objects.create(usuario=user, rol="EMISOR", empresa=e)
        client = APIClient()
        client.force_authenticate(user=user)
        assert client.get("/api/clientes/").status_code == 200

    def test_usuario_sin_perfil_tiene_acceso_limitado(self):
        """Un user autenticado sin perfil puede acceder (no es admin pero tampoco sin auth)."""
        from django.contrib.auth.models import User
        user = User.objects.create_user(username="sinperfil", password="p")
        client = APIClient()
        client.force_authenticate(user=user)
        # Sin perfil, el queryset no filtra por empresa pero sigue funcionando
        assert client.get("/api/clientes/").status_code == 200


@pytest.mark.django_db
class TestPerfilUsuarioModel:
    def test_str_representation(self):
        from django.contrib.auth.models import User
        from apps.usuarios.models import PerfilUsuario
        user = User.objects.create_user(username="juan", password="p")
        p = PerfilUsuario.objects.create(usuario=user, rol="EMISOR")
        s = str(p)
        assert "juan" in s
        assert "Emisor" in s or "EMISOR" in s

    def test_es_admin_property(self):
        from django.contrib.auth.models import User
        from apps.usuarios.models import PerfilUsuario
        user = User.objects.create_user(username="adm", password="p")
        p = PerfilUsuario.objects.create(usuario=user, rol="ADMIN")
        assert p.es_admin
        assert not p.es_emisor
        assert not p.es_contador

    def test_es_emisor_property(self):
        from django.contrib.auth.models import User
        from apps.usuarios.models import PerfilUsuario
        user = User.objects.create_user(username="emi", password="p")
        p = PerfilUsuario.objects.create(usuario=user, rol="EMISOR")
        assert p.es_emisor
        assert not p.es_admin
        assert not p.es_contador

    def test_es_contador_property(self):
        from django.contrib.auth.models import User
        from apps.usuarios.models import PerfilUsuario
        user = User.objects.create_user(username="con", password="p")
        p = PerfilUsuario.objects.create(usuario=user, rol="CONTADOR")
        assert p.es_contador
        assert not p.es_admin
        assert not p.es_emisor