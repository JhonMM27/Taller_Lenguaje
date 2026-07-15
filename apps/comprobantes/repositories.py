"""
Backward-compatibility: repositorios que retornan modelos Django.

Las views/servicios legacy (`apps.sunat_ose.services`, etc.) esperan que
`obtener_por_id` retorne un MODELO Django (con `.empresa`, `.cliente`, etc.),
no una entidad de dominio.

Estos wrappers NO son el repositorio hexagonal; son shims que usan
Django ORM directamente para preservar la API legacy.
"""
from decimal import Decimal
from typing import Optional


class ComprobanteRepositoryDjango:
    """Wrapper legacy: retorna modelos Django ORM."""

    def obtener_por_id(self, comprobante_id: int):
        from apps.comprobantes.models import Comprobante as CompModel
        try:
            return CompModel.objects.select_related(
                'cliente', 'empresa', 'serie'
            ).get(pk=comprobante_id, activo=True)
        except CompModel.DoesNotExist as exc:
            from dominio.excepciones import ComprobanteNoEncontrado
            raise ComprobanteNoEncontrado(
                f"Comprobante {comprobante_id} no existe"
            ) from exc

    def listar(
        self,
        empresa_id: Optional[int] = None,
        cliente_id: Optional[int] = None,
        tipo: str = '',
        estado: str = '',
        fecha_desde=None,
        fecha_hasta=None,
        ruc_cliente: str = '',
        limit: int = 50,
    ):
        from apps.comprobantes.models import Comprobante as CompModel
        qs = CompModel.objects.select_related('cliente', 'empresa', 'serie')
        qs = qs.filter(activo=True)
        if empresa_id is not None:
            qs = qs.filter(empresa_id=empresa_id)
        if cliente_id is not None:
            qs = qs.filter(cliente_id=cliente_id)
        if tipo:
            qs = qs.filter(tipo=tipo)
        if estado:
            qs = qs.filter(estado=estado)
        if fecha_desde:
            qs = qs.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha__lte=fecha_hasta)
        if ruc_cliente:
            qs = qs.filter(cliente__num_doc__icontains=ruc_cliente)
        return list(qs.order_by('-fecha', '-creado_en')[:limit])

    def guardar(self, comprobante) -> None:
        """Guarda un modelo Django (acepta modelo, no entidad)."""
        comprobante.save()

    def eliminar_soft(self, comprobante_id: int, usuario_id: Optional[int] = None) -> None:
        from apps.comprobantes.models import Comprobante as CompModel
        m = CompModel.objects.filter(pk=comprobante_id).first()
        if m:
            m.eliminar(usuario=None)

    def existe_serie_numero(self, serie_id: int, numero: int) -> bool:
        from apps.comprobantes.models import Comprobante as CompModel
        return CompModel.objects.filter(
            serie_id=serie_id, numero=numero, activo=True
        ).exists()


class SerieRepositoryDjango:
    """Wrapper legacy para series."""

    def obtener_o_crear(self, empresa_id: int, tipo: str):
        from apps.comprobantes.models import SerieComprobante as SerieModel
        defaults_serie = {
            '01': 'F001',
            '03': 'B001',
            '07': 'FC01',
            '08': 'FD01',
        }
        serie_obj, created = SerieModel.objects.select_for_update().get_or_create(
            empresa_id=empresa_id,
            tipo=tipo,
            activo=True,
            defaults={
                'serie': defaults_serie.get(tipo, 'X001'),
                'correlativo_actual': 0,
            },
        )
        return serie_obj, created

    def siguiente_correlativo(self, empresa_id: int, tipo: str):
        from apps.comprobantes.models import SerieComprobante as SerieModel
        from apps.comprobantes.models import Comprobante as CompModel
        from django.db.models import Max
        serie_obj, _ = self.obtener_o_crear(empresa_id, tipo)
        max_numero_real = CompModel.objects.filter(
            serie_id=serie_obj.id
        ).aggregate(Max('numero'))['numero__max'] or 0
        siguiente = max(serie_obj.correlativo_actual, max_numero_real) + 1
        serie_obj.correlativo_actual = siguiente
        serie_obj.save(update_fields=['correlativo_actual'])
        return serie_obj, siguiente

    def guardar(self, serie) -> None:
        serie.save()


__all__ = ['ComprobanteRepositoryDjango', 'SerieRepositoryDjango']
