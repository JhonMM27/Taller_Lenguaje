"""
Backward-compatibility: re-exporta el service de dominio NC.
"""
from interfaces.container import get_nota_credito_service


def _modelo_desde_entidad(ent):
    if ent is None or ent.id is None:
        return None
    from apps.notas_credito.models import NotaCredito as NCModel
    return NCModel.objects.select_related(
        'comprobante_referencia',
        'comprobante_referencia__cliente',
    ).get(pk=ent.id)


class NotaCreditoService:
    """Wrapper backward-compatible para views/templates."""

    @staticmethod
    def emitir(data, usuario=None):
        creado_por_id = usuario.id if usuario else None
        service = get_nota_credito_service()
        monto_afectado = data.get('monto_afectado')
        ent = service.emitir(
            comprobante_referencia_id=data['comprobante_id'],
            tipo_nc=data.get('tipo_nc', 'NC'),
            tipo_nota=data.get('tipo_nota', '01'),
            descripcion=data.get('descripcion', ''),
            detalles_data=data.get('detalles'),
            creado_por_id=creado_por_id,
            monto_afectado=monto_afectado,
        )
        return _modelo_desde_entidad(ent)

    @staticmethod
    def eliminar(nota_id, usuario=None):
        return get_nota_credito_service().eliminar(
            nota_id=nota_id,
            usuario_id=usuario.id if usuario else None,
        )


__all__ = ['NotaCreditoService']