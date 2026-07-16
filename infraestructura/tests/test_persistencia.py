"""
Tests de la capa de infraestructura (adaptadores Django ORM).

Estos tests verifican que los mappers y los repositorios funcionan
correctamente con la base de datos SQLite de tests.
"""
import pytest
from decimal import Decimal
from datetime import date

from dominio.entidades.comprobante import Comprobante, DetalleComprobante
from dominio.entidades.cliente import Cliente
from dominio.entidades.producto import Producto
from dominio.entidades.empresa import Empresa
from dominio.excepciones import (
    ClienteNoEncontrado,
    EmpresaNoEncontrada,
    ProductoNoEncontrado,
)


@pytest.mark.django_db
class TestMappers:
    def test_cliente_roundtrip(self):
        ent = Cliente(
            id=None, tipo_doc="6", num_doc="20100000001",
            razon_social="Test SA", direccion="Av Test 123",
        )
        from infraestructura.persistencia.mappers import (
            cliente_a_modelo, modelo_a_cliente,
        )
        from apps.clientes.models import Cliente as ClienteModel
        m = cliente_a_modelo(ent)
        m.save()
        loaded = modelo_a_cliente(ClienteModel.objects.get(pk=m.pk))
        assert loaded.razon_social == "Test SA"
        assert loaded.tipo_doc == "6"

    def test_producto_roundtrip(self):
        ent = Producto(
            id=None, descripcion="Prod",
            precio_unitario=Decimal("99.50"),
            afecto_igv=True,
        )
        from infraestructura.persistencia.mappers import (
            producto_a_modelo, modelo_a_producto,
        )
        from apps.productos.models import Producto as ProductoModel
        m = producto_a_modelo(ent)
        m.save()
        loaded = modelo_a_producto(ProductoModel.objects.get(pk=m.pk))
        assert loaded.descripcion == "Prod"
        assert loaded.precio_unitario == Decimal("99.50")

    def test_empresa_roundtrip(self):
        ent = Empresa(
            id=None, ruc="20999999999", razon_social="Test",
            regimen_tributario="MYPE",
        )
        from infraestructura.persistencia.mappers import (
            empresa_a_modelo, modelo_a_empresa,
        )
        from apps.empresas.models import Empresa as EmpresaModel
        m = empresa_a_modelo(ent)
        m.save()
        loaded = modelo_a_empresa(EmpresaModel.objects.get(pk=m.pk))
        assert loaded.ruc == "20999999999"
        assert loaded.regimen_tributario == "MYPE"


@pytest.mark.django_db
class TestDjangoClienteRepository:
    def test_obtener_por_id_ok(self):
        from apps.clientes.models import Cliente
        from infraestructura.persistencia import DjangoClienteRepository
        c = Cliente.objects.create(
            tipo_doc="6", num_doc="20999999999", razon_social="X",
        )
        repo = DjangoClienteRepository()
        loaded = repo.obtener_por_id(c.pk)
        assert loaded.razon_social == "X"

    def test_obtener_por_id_no_existe(self):
        from infraestructura.persistencia import DjangoClienteRepository
        repo = DjangoClienteRepository()
        with pytest.raises(ClienteNoEncontrado):
            repo.obtener_por_id(99999)

    def test_buscar(self):
        from apps.clientes.models import Cliente
        from infraestructura.persistencia import DjangoClienteRepository
        Cliente.objects.create(tipo_doc="6", num_doc="20999999991", razon_social="Alpha SA")
        Cliente.objects.create(tipo_doc="6", num_doc="20999999992", razon_social="Beta SA")
        repo = DjangoClienteRepository()
        results = repo.buscar(query="Alpha")
        assert len(results) == 1
        assert results[0].razon_social == "Alpha SA"

    def test_guardar_nuevo(self):
        from infraestructura.persistencia import DjangoClienteRepository
        repo = DjangoClienteRepository()
        ent = Cliente(
            id=None, tipo_doc="1", num_doc="12345678",
            razon_social="Juan",
        )
        saved = repo.guardar(ent)
        assert saved.id is not None

    def test_eliminar_soft(self):
        from apps.clientes.models import Cliente
        from infraestructura.persistencia import DjangoClienteRepository
        c = Cliente.objects.create(
            tipo_doc="6", num_doc="20999999993", razon_social="X",
        )
        repo = DjangoClienteRepository()
        repo.eliminar_soft(c.pk)
        c.refresh_from_db()
        assert not c.activo


@pytest.mark.django_db
class TestDjangoProductoRepository:
    def test_obtener_por_id_ok(self):
        from apps.productos.models import Producto
        from infraestructura.persistencia import DjangoProductoRepository
        p = Producto.objects.create(
            descripcion="P", precio_unitario=Decimal("10"),
        )
        repo = DjangoProductoRepository()
        loaded = repo.obtener_por_id(p.pk)
        assert loaded.descripcion == "P"

    def test_obtener_por_id_no_existe(self):
        from infraestructura.persistencia import DjangoProductoRepository
        repo = DjangoProductoRepository()
        with pytest.raises(ProductoNoEncontrado):
            repo.obtener_por_id(99999)

    def test_buscar(self):
        from apps.productos.models import Producto
        from infraestructura.persistencia import DjangoProductoRepository
        Producto.objects.create(descripcion="Laptop Dell", precio_unitario=Decimal("1500"))
        Producto.objects.create(descripcion="Mouse", precio_unitario=Decimal("50"))
        repo = DjangoProductoRepository()
        results = repo.buscar(query="Laptop")
        assert len(results) == 1
        assert "Laptop" in results[0].descripcion

    def test_guardar(self):
        from infraestructura.persistencia import DjangoProductoRepository
        repo = DjangoProductoRepository()
        ent = Producto(
            id=None, descripcion="Nuevo",
            precio_unitario=Decimal("99"),
        )
        saved = repo.guardar(ent)
        assert saved.id is not None


@pytest.mark.django_db
class TestDjangoEmpresaRepository:
    def test_obtener_por_id_ok(self):
        from apps.empresas.models import Empresa
        from infraestructura.persistencia import DjangoEmpresaRepository
        e = Empresa.objects.create(ruc="20999999999", razon_social="X")
        repo = DjangoEmpresaRepository()
        loaded = repo.obtener_por_id(e.pk)
        assert loaded.razon_social == "X"

    def test_obtener_por_id_no_existe(self):
        from infraestructura.persistencia import DjangoEmpresaRepository
        repo = DjangoEmpresaRepository()
        with pytest.raises(EmpresaNoEncontrada):
            repo.obtener_por_id(99999)

    def test_listar(self):
        from apps.empresas.models import Empresa
        from infraestructura.persistencia import DjangoEmpresaRepository
        Empresa.objects.create(ruc="20999999991", razon_social="A")
        Empresa.objects.create(ruc="20999999992", razon_social="B")
        repo = DjangoEmpresaRepository()
        empresas = repo.listar()
        assert len(empresas) >= 2


@pytest.mark.django_db
class TestDjangoSerieComprobanteRepository:
    def test_obtener_o_crear_nuevo(self):
        from apps.empresas.models import Empresa
        from infraestructura.persistencia import DjangoSerieComprobanteRepository
        e = Empresa.objects.create(ruc="20999999999", razon_social="X")
        repo = DjangoSerieComprobanteRepository()
        s, created = repo.obtener_o_crear(e.id, "01")
        assert created
        assert s.tipo == "01"

    def test_obtener_o_crear_existente(self):
        from apps.empresas.models import Empresa
        from apps.comprobantes.models import SerieComprobante
        from infraestructura.persistencia import DjangoSerieComprobanteRepository
        e = Empresa.objects.create(ruc="20999999999", razon_social="X")
        SerieComprobante.objects.create(
            empresa=e, tipo="01", serie="F001", correlativo_actual=5,
        )
        repo = DjangoSerieComprobanteRepository()
        s, created = repo.obtener_o_crear(e.id, "01")
        assert not created
        assert s.serie == "F001"

    def test_siguiente_correlativo(self):
        from apps.empresas.models import Empresa
        from infraestructura.persistencia import DjangoSerieComprobanteRepository
        e = Empresa.objects.create(ruc="20999999999", razon_social="X")
        repo = DjangoSerieComprobanteRepository()
        s, n1 = repo.siguiente_correlativo(e.id, "01")
        assert n1 == 1
        s, n2 = repo.siguiente_correlativo(e.id, "01")
        assert n2 == 2


@pytest.mark.django_db
class TestDjangoComprobanteRepository:
    def test_guardar_y_obtener(self):
        from apps.empresas.models import Empresa
        from apps.clientes.models import Cliente
        from apps.productos.models import Producto
        from apps.comprobantes.models import Comprobante as CompModel, DetalleComprobante
        from infraestructura.persistencia import DjangoComprobanteRepository, DjangoSerieComprobanteRepository
        from dominio.entidades.comprobante import DetalleComprobante as DetEnt

        e = Empresa.objects.create(ruc="20999999999", razon_social="X")
        c = Cliente.objects.create(
            tipo_doc="6", num_doc="20100000002", razon_social="C",
        )
        p = Producto.objects.create(
            descripcion="P", precio_unitario=Decimal("100"),
        )
        # Crear serie y obtener correlativo
        s_repo = DjangoSerieComprobanteRepository()
        s, num = s_repo.siguiente_correlativo(e.id, "01")

        ent = Comprobante(
            id=None, empresa_id=e.id, cliente_id=c.id, serie_id=s.id,
            numero=num, fecha=date.today(), tipo="01",
            detalles=[
                DetEnt(
                    id=None, producto_id=p.id,
                    cantidad=Decimal("2"),
                    precio_unitario=Decimal("100"),
                    afecto_igv=True,
                ),
            ],
        )
        repo = DjangoComprobanteRepository()
        saved = repo.guardar(ent)
        assert saved.id is not None

        # Obtener de vuelta
        loaded = repo.obtener_por_id(saved.id)
        assert loaded.numero == num

    def test_listar_con_filtros(self):
        from apps.empresas.models import Empresa
        from apps.clientes.models import Cliente
        from apps.productos.models import Producto
        from apps.comprobantes.models import (
            Comprobante as CompModel,
            DetalleComprobante,
            SerieComprobante,
        )
        from infraestructura.persistencia import DjangoComprobanteRepository

        e = Empresa.objects.create(ruc="20999999999", razon_social="X")
        c = Cliente.objects.create(
            tipo_doc="6", num_doc="20100000003", razon_social="C",
        )
        p = Producto.objects.create(descripcion="P", precio_unitario=Decimal("100"))
        s = SerieComprobante.objects.create(
            empresa=e, tipo="01", serie="F001",
        )
        comp = CompModel.objects.create(
            empresa=e, cliente=c, serie=s, numero=1,
            fecha=date.today(), tipo="01", estado="BORRADOR",
        )
        DetalleComprobante.objects.create(
            comprobante=comp, producto=p,
            cantidad=Decimal("1"), precio_unitario=Decimal("100"),
            afecto_igv=True,
        )
        repo = DjangoComprobanteRepository()
        result = repo.listar(empresa_id=e.id)
        assert len(result) == 1
        assert result[0].tipo == "01"

    def test_eliminar_soft(self):
        from apps.empresas.models import Empresa
        from apps.clientes.models import Cliente
        from apps.comprobantes.models import Comprobante as CompModel, SerieComprobante
        from infraestructura.persistencia import DjangoComprobanteRepository

        e = Empresa.objects.create(ruc="20999999999", razon_social="X")
        c = Cliente.objects.create(
            tipo_doc="6", num_doc="20100000004", razon_social="C",
        )
        s = SerieComprobante.objects.create(empresa=e, tipo="01", serie="F001")
        comp = CompModel.objects.create(
            empresa=e, cliente=c, serie=s, numero=1,
            fecha=date.today(), tipo="01", estado="BORRADOR",
        )
        repo = DjangoComprobanteRepository()
        repo.eliminar_soft(comp.pk)
        comp.refresh_from_db()
        assert not comp.activo


@pytest.mark.django_db
class TestDjangoNotaCreditoRepository:
    def test_siguiente_numero(self):
        from apps.empresas.models import Empresa
        from apps.clientes.models import Cliente
        from apps.comprobantes.models import (
            Comprobante as CompModel, SerieComprobante,
        )
        from apps.notas_credito.models import NotaCredito as NCModel
        from infraestructura.persistencia import DjangoNotaCreditoRepository

        e = Empresa.objects.create(ruc="20999999999", razon_social="X")
        c = Cliente.objects.create(
            tipo_doc="6", num_doc="20100000005", razon_social="C",
        )
        s = SerieComprobante.objects.create(empresa=e, tipo="01", serie="F001")
        comp = CompModel.objects.create(
            empresa=e, cliente=c, serie=s, numero=1,
            fecha=date.today(), tipo="01", estado="ACEPTADO",
        )
        NCModel.objects.create(
            comprobante_referencia=comp, serie="FC01", numero=1,
            fecha=date.today(), tipo_nc="NC", tipo_nota="01",
            estado="BORRADOR",
        )
        repo = DjangoNotaCreditoRepository()
        nxt = repo.siguiente_numero("FC01")
        assert nxt == 2


@pytest.mark.django_db
class TestDjangoLogSunatRepository:
    def test_registrar(self):
        from apps.empresas.models import Empresa
        from apps.clientes.models import Cliente
        from apps.comprobantes.models import (
            Comprobante as CompModel, SerieComprobante,
        )
        from infraestructura.persistencia import (
            DjangoLogSunatRepository,
            DjangoComprobanteRepository,
        )
        e = Empresa.objects.create(ruc="20999999999", razon_social="X")
        c = Cliente.objects.create(
            tipo_doc="6", num_doc="20100000006", razon_social="C",
        )
        s = SerieComprobante.objects.create(empresa=e, tipo="01", serie="F001")
        comp = CompModel.objects.create(
            empresa=e, cliente=c, serie=s, numero=1,
            fecha=date.today(), tipo="01", estado="ACEPTADO",
        )
        loaded_comp = DjangoComprobanteRepository().obtener_por_id(comp.pk)
        log_repo = DjangoLogSunatRepository()
        log_repo.registrar(
            loaded_comp,
            estado_respuesta="ACEPTADO",
            codigo_respuesta="0",
            descripcion="OK",
            uuid="ticket-123",
            cdr_xml="cdr-base64",
        )
        logs = log_repo.obtener_por_comprobante(comp.pk)
        assert len(logs) == 1


@pytest.mark.django_db
class TestDjangoUnitOfWork:
    def test_context_manager(self):
        from infraestructura.persistencia import DjangoUnitOfWork
        with DjangoUnitOfWork() as uow:
            assert uow.comprobantes is not None
            assert uow.notas_credito is not None
            assert uow.series is not None
            assert uow.clientes is not None
            assert uow.productos is not None
            assert uow.empresas is not None
            assert uow.logs_sunat is not None