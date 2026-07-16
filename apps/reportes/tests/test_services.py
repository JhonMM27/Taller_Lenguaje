"""
Tests del servicio de reportes.
"""
import pytest
from decimal import Decimal
from datetime import date


@pytest.fixture
def comprobantes_mes(db):
    from apps.empresas.models import Empresa
    from apps.clientes.models import Cliente
    from apps.comprobantes.models import (
        Comprobante, DetalleComprobante, SerieComprobante,
    )
    from apps.productos.models import Producto
    e = Empresa.objects.create(ruc="20999999999", razon_social="X")
    c = Cliente.objects.create(
        tipo_doc="6", num_doc="20100000001", razon_social="X",
    )
    p = Producto.objects.create(
        descripcion="X", precio_unitario=Decimal("100"),
    )
    s = SerieComprobante.objects.create(empresa=e, tipo="01", serie="F001")
    s2 = SerieComprobante.objects.create(empresa=e, tipo="03", serie="B001")

    today = date.today()
    c1 = Comprobante.objects.create(
        empresa=e, cliente=c, serie=s, numero=1,
        fecha=today, tipo="01", estado="ACEPTADO",
        subtotal=Decimal("100"), igv=Decimal("18"), total=Decimal("118"),
    )
    DetalleComprobante.objects.create(
        comprobante=c1, producto=p,
        cantidad=Decimal("1"), precio_unitario=Decimal("100"),
        afecto_igv=True,
    )
    c2 = Comprobante.objects.create(
        empresa=e, cliente=c, serie=s2, numero=1,
        fecha=today, tipo="03", estado="ACEPTADO",
        subtotal=Decimal("50"), igv=Decimal("9"), total=Decimal("59"),
    )
    DetalleComprobante.objects.create(
        comprobante=c2, producto=p,
        cantidad=Decimal("1"), precio_unitario=Decimal("50"),
        afecto_igv=True,
    )
    return c1, c2


@pytest.mark.django_db
class TestReporteService:
    def test_ventas_por_periodo(self, comprobantes_mes):
        from apps.reportes.services import ReporteService
        resultado = ReporteService.ventas_por_periodo(
            mes=date.today().month,
            anio=date.today().year,
        )
        assert "data" in resultado
        assert "resumen" in resultado
        assert len(resultado["data"]) == 2

    def test_ventas_por_periodo_sin_datos(self, db):
        from apps.reportes.services import ReporteService
        resultado = ReporteService.ventas_por_periodo(mes=1, anio=1999)
        assert resultado["data"] == []

    def test_dashboard_resumen(self, comprobantes_mes):
        from apps.reportes.services import ReporteService
        resumen = ReporteService.dashboard_resumen()
        assert "facturas_mes" in resumen
        assert "boletas_mes" in resumen
        assert "aceptadas_mes" in resumen
        assert "rechazadas_mes" in resumen
        assert resumen["facturas_mes"] >= 1
        assert resumen["boletas_mes"] >= 1

    def test_dashboard_sin_datos(self, db):
        from apps.reportes.services import ReporteService
        resumen = ReporteService.dashboard_resumen()
        assert resumen["facturas_mes"] >= 0
        assert resumen["total_ventas"] == "0.00"