"""
Backward-compatibility: re-exporta el service de dominio desde `interfaces.container`.

Las views viejas hacen `from apps.comprobantes.services import ComprobanteService`.
Para no romperlas, este modulo expone una clase-compatible que delega al
servicio del dominio via DI y devuelve modelos Django ORM (manteniendo
la firma original).
"""
from interfaces.container import (
    get_comprobante_service,
    get_uow,
)


def _modelo_desde_entidad(ent):
    """Helper: dado una entidad de dominio, devuelve el modelo Django."""
    if ent is None or ent.id is None:
        return None
    from apps.comprobantes.models import Comprobante as CompModel
    return CompModel.objects.select_related(
        'cliente', 'empresa', 'serie'
    ).get(pk=ent.id)


class ComprobanteService:
    """Wrapper backward-compatible para views/templates que importan
    desde `apps.comprobantes.services`.

    Mantiene la firma clasica (devuelve modelos Django) pero delega
    a la nueva capa hexagonal.
    """

    @staticmethod
    def crear(data, usuario=None):
        creado_por_id = usuario.id if usuario else None
        detalles = data.get('detalles', [])
        service = get_comprobante_service()
        ent = service.crear(
            empresa_id=data['empresa_id'],
            cliente_id=data['cliente_id'],
            fecha=data['fecha'],
            tipo=data['tipo'],
            detalles_data=detalles,
            creado_por_id=creado_por_id,
        )
        return _modelo_desde_entidad(ent)

    @staticmethod
    def emitir(comprobante_id):
        ent = get_comprobante_service().emitir(comprobante_id=comprobante_id)
        return _modelo_desde_entidad(ent)

    @staticmethod
    def reenviar(comprobante_id):
        ent = get_comprobante_service().reenviar(comprobante_id=comprobante_id)
        return _modelo_desde_entidad(ent)

    @staticmethod
    def eliminar(comprobante_id, usuario=None):
        return get_comprobante_service().eliminar(
            comprobante_id=comprobante_id,
            usuario_id=usuario.id if usuario else None,
        )

    @staticmethod
    def cambiar_estado(comprobante_id, nuevo_estado):
        from interfaces.container import get_uow, get_comprobante_service
        service = get_comprobante_service()
        comp_ent = service.obtener(comprobante_id=comprobante_id)
        comp_ent.cambiar_estado(nuevo_estado)
        with get_uow():
            get_uow().comprobantes.guardar(comp_ent)
            get_uow().commit()
        return _modelo_desde_entidad(comp_ent)


class NumeracionService:
    """Wrapper backward-compatible para NumeracionService."""

    @staticmethod
    def siguiente_correlativo(empresa, tipo):
        from interfaces.container import get_uow
        return get_uow().series.siguiente_correlativo(empresa.id, tipo)


__all__ = ['ComprobanteService', 'NumeracionService']