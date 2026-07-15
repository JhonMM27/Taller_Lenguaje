"""
Permisos personalizados basados en los roles de PerfilUsuario.
"""

from rest_framework import permissions


class IsAdminUserRole(permissions.BasePermission):
    """Permite el acceso únicamente a usuarios con rol ADMIN."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and 
            user.is_authenticated and 
            hasattr(user, 'perfil') and 
            user.perfil.rol == 'ADMIN'
        )


class IsEmisorUserRole(permissions.BasePermission):
    """Permite el acceso a usuarios con rol EMISOR u ADMIN."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and 
            user.is_authenticated and 
            hasattr(user, 'perfil') and 
            user.perfil.rol in ('ADMIN', 'EMISOR')
        )


class IsContadorUserRole(permissions.BasePermission):
    """Permite el acceso a usuarios con rol CONTADOR u ADMIN."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and 
            user.is_authenticated and 
            hasattr(user, 'perfil') and 
            user.perfil.rol in ('ADMIN', 'CONTADOR')
        )
