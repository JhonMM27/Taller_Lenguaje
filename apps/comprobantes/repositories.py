"""
Repository Pattern para el módulo de Comprobantes.

Abstrae el acceso a datos. El Service usa la interfaz (Protocol),
no el ORM directamente. Facilita mock en tests y desacopla la persistencia.
"""

from typing import Protocol, Optional
from decimal import Decimal
from django.db.models import Max, QuerySet

from apps.comprobantes.models import Comprobante, SerieComprobante, DetalleComprobante
from apps.core.exceptions import ComprobanteNoEncontrado, SerieNoEncontrada


# ──────────────────────────────────────────────────────────────
# Puertos (Interfaces) — Protocol
# ──────────────────────────────────────────────────────────────

class IComprobanteRepository(Protocol):
    """Interface para el repositorio de comprobantes."""

    def obtener_por_id(self, comprobante_id: int) -> Comprobante:
        """Obtiene un comprobante por su ID. Lanza ComprobanteNoEncontrado si no existe."""
        ...

    def listar_por_filtros(
        self,
        tipo: str = '',
        estado: str = '',
        fecha_desde: str = '',
        fecha_hasta: str = '',
        cliente_id: int = None,
        ruc_cliente: str = '',
        limit: int = 50,
    ) -> QuerySet:
        """Lista comprobantes con filtros opcionales."""
        ...

    def guardar(self, comprobante: Comprobante) -> None:
        """Persiste un comprobante."""
        ...

    def obtener_siguiente_numero(self, serie: SerieComprobante) -> int:
        """Obtiene el siguiente número correlativo para una serie."""
        ...

    def buscar_por_serie_numero(self, serie: str, numero: int) -> list:
        """Busca comprobantes por serie y número."""
        ...


class ISerieRepository(Protocol):
    """Interface para el repositorio de series de comprobante."""

    def obtener_o_crear(self, empresa_id: int, tipo: str) -> tuple:
        """Obtiene o crea una serie con select_for_update."""
        ...


# ──────────────────────────────────────────────────────────────
# Adaptadores (Implementaciones Django ORM)
# ──────────────────────────────────────────────────────────────

class ComprobanteRepositoryDjango:
    """Implementación del repositorio de comprobantes usando Django ORM."""

    def obtener_por_id(self, comprobante_id: int) -> Comprobante:
        try:
            return Comprobante.objects.select_related(
                'cliente', 'empresa', 'serie'
            ).get(pk=comprobante_id, activo=True)
        except Comprobante.DoesNotExist:
            raise ComprobanteNoEncontrado(
                f"Comprobante {comprobante_id} no existe"
            )

    def listar_por_filtros(
        self,
        tipo: str = '',
        estado: str = '',
        fecha_desde: str = '',
        fecha_hasta: str = '',
        cliente_id: int = None,
        ruc_cliente: str = '',
        limit: int = 50,
    ) -> QuerySet:
        queryset = Comprobante.objects.select_related(
            'cliente', 'empresa', 'serie'
        ).filter(activo=True)

        if tipo:
            queryset = queryset.filter(tipo=tipo)
        if estado:
            queryset = queryset.filter(estado=estado)
        if fecha_desde:
            queryset = queryset.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha__lte=fecha_hasta)
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        if ruc_cliente:
            queryset = queryset.filter(cliente__num_doc__icontains=ruc_cliente)

        return queryset.order_by('-fecha', '-creado_en')[:limit]

    def guardar(self, comprobante: Comprobante) -> None:
        comprobante.save()

    def obtener_siguiente_numero(self, serie: SerieComprobante) -> int:
        max_numero = Comprobante.objects.filter(
            serie=serie
        ).aggregate(Max('numero'))['numero__max'] or 0
        return max(serie.correlativo_actual, max_numero) + 1

    def buscar_por_serie_numero(self, serie: str, numero: int) -> list:
        comprobantes = Comprobante.objects.filter(
            serie__serie=serie,
            numero=numero,
            activo=True,
        ).select_related('cliente', 'empresa', 'serie')

        return [
            {
                'id': comp.id,
                'numero': f"{comp.serie.serie}-{comp.numero:08d}",
                'cliente': comp.cliente.razon_social,
                'ruc': comp.cliente.num_doc,
                'fecha': comp.fecha.strftime('%Y-%m-%d'),
                'total': float(comp.total),
                'estado': comp.estado,
            }
            for comp in comprobantes
        ]


class SerieRepositoryDjango:
    """Implementación del repositorio de series usando Django ORM."""

    SERIE_DEFAULTS = {
        '01': 'F001',
        '03': 'B001',
        '07': 'FC01',
        '08': 'FD01',
    }

    def obtener_o_crear(self, empresa_id: int, tipo: str) -> tuple:
        from apps.empresas.models import Empresa
        empresa = Empresa.objects.get(id=empresa_id)

        serie_obj, created = SerieComprobante.objects.select_for_update().get_or_create(
            empresa=empresa,
            tipo=tipo,
            defaults={
                'serie': self.SERIE_DEFAULTS.get(tipo, 'X001'),
                'correlativo_actual': 0,
            }
        )

        if not created:
            serie_obj.refresh_from_db()

        return serie_obj, created
