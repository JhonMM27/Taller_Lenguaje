"""
Backward-compatibility: re-exporta el service de dominio desde `interfaces.container`.

Las views viejas hacen `from apps.comprobantes.services import ComprobanteService`.
Para no romperlas, este modulo expone una clase-compatible que delega al
servicio del dominio via DI y devuelve modelos Django ORM (manteniendo
la firma original).
"""
import logging

from interfaces.container import (
    get_comprobante_service,
    get_uow,
)


logger = logging.getLogger(__name__)


def _modelo_desde_entidad(ent):
    """Helper: dado una entidad de dominio, devuelve el modelo Django."""
    if ent is None or ent.id is None:
        return None
    from apps.comprobantes.models import Comprobante as CompModel
    return CompModel.objects.select_related(
        'cliente', 'empresa', 'serie'
    ).get(pk=ent.id)


def _generar_y_firmar_xml(comprobante_model):
    """
    Genera el XML UBL 2.1 del comprobante y lo firma digitalmente.

    Retorna el XML firmado (str) o None si falla.
    """
    try:
        from apps.sunat_ose.xml_generator import generar_xml_ubl
        from apps.sunat_ose.firmar import firmar_xml

        xml_content = generar_xml_ubl(comprobante_model)
        xml_firmado = firmar_xml(xml_content, empresa_id=comprobante_model.empresa_id)
        if isinstance(xml_firmado, bytes):
            return xml_firmado.decode('utf-8')
        return xml_firmado
    except Exception as exc:
        logger.exception("Error generando/firmando XML para comprobante %s", comprobante_model.pk)
        return None


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
        """
        Cambia estado BORRADOR -> EMITIDO y genera el XML firmado.
        """
        ent = get_comprobante_service().emitir(comprobante_id=comprobante_id)
        # Generar XML firmado en el modelo Django
        modelo = _modelo_desde_entidad(ent)
        if modelo is not None:
            xml_firmado = _generar_y_firmar_xml(modelo)
            if xml_firmado:
                modelo.xml_firmado = xml_firmado
                modelo.save(update_fields=['xml_firmado'])
        return modelo

    @staticmethod
    def reenviar(comprobante_id):
        """
        Regenera XML de un comprobante RECHAZADO y cambia estado a ENVIADO.
        """
        ent = get_comprobante_service().reenviar(comprobante_id=comprobante_id)
        modelo = _modelo_desde_entidad(ent)
        if modelo is not None:
            xml_firmado = _generar_y_firmar_xml(modelo)
            if xml_firmado:
                modelo.xml_firmado = xml_firmado
                modelo.save(update_fields=['xml_firmado'])
        return modelo

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