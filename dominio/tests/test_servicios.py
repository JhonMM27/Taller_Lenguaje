"""
Tests del dominio: servicios con mocks (sin BD, sin Django).

Demuestra que los servicios del dominio son testeables sin infraestructura.
"""
import pytest
from decimal import Decimal
from datetime import date
from typing import Optional

from dominio.entidades.comprobante import (
    Comprobante,
    DetalleComprobante,
    SerieComprobante,
    ESTADO_BORRADOR,
    ESTADO_EMITIDO,
    TIPO_FACTURA,
    TIPO_BOLETA,
)
from dominio.entidades.nota_credito import NotaCredito
from dominio.entidades.cliente import Cliente
from dominio.entidades.producto import Producto
from dominio.entidades.empresa import Empresa
from dominio.excepciones import (
    TipoDocumentoInvalido,
    EstadoInvalido,
    ComprobanteNoAnulable,
    ComprobanteNoAceptado,
    MontoExcedidoError,
    RecursoNoEncontrado,
    ProductoNoEncontrado,
    ClienteNoEncontrado,
    EmpresaNoEncontrada,
    SerieNoEncontrada,
)
from dominio.servicios import ComprobanteService, NotaCreditoService


# ============================================================
# Mocks - implementaciones in-memory de los puertos
# ============================================================

class MockComprobanteRepo:
    def __init__(self):
        self._store = {}
        self._next_id = 1

    def obtener_por_id(self, comprobante_id):
        if comprobante_id not in self._store:
            from dominio.excepciones import ComprobanteNoEncontrado
            raise ComprobanteNoEncontrado(f"no existe {comprobante_id}")
        return self._store[comprobante_id]

    def listar(self, **kwargs):
        return list(self._store.values())

    def guardar(self, comprobante):
        if comprobante.id is None:
            comprobante.id = self._next_id
            self._next_id += 1
        self._store[comprobante.id] = comprobante
        return comprobante

    def eliminar_soft(self, comprobante_id, usuario_id=None):
        if comprobante_id in self._store:
            self._store[comprobante_id].activo = False

    def existe_serie_numero(self, serie_id, numero):
        return any(c.serie_id == serie_id and c.numero == numero for c in self._store.values())


class MockNotaCreditoRepo:
    def __init__(self):
        self._store = {}
        self._next_id = 1

    def obtener_por_id(self, nota_id):
        if nota_id not in self._store:
            from dominio.excepciones import NotaCreditoNoEncontrada
            raise NotaCreditoNoEncontrada(f"no existe {nota_id}")
        return self._store[nota_id]

    def listar(self, **kwargs):
        return list(self._store.values())

    def guardar(self, nota):
        if nota.id is None:
            nota.id = self._next_id
            self._next_id += 1
        self._store[nota.id] = nota
        return nota

    def eliminar_soft(self, nota_id, usuario_id=None):
        if nota_id in self._store:
            self._store[nota_id].activo = False

    def siguiente_numero(self, serie):
        return sum(1 for n in self._store.values() if n.serie == serie) + 1


class MockSerieRepo:
    def __init__(self):
        self._store = {}
        self._next_id = 1

    def obtener_o_crear(self, empresa_id, tipo):
        key = (empresa_id, tipo)
        if key in self._store:
            return self._store[key], False
        s = SerieComprobante(
            id=self._next_id, empresa_id=empresa_id, tipo=tipo,
            serie="F001" if tipo == "01" else "B001",
            correlativo_actual=0,
        )
        self._next_id += 1
        self._store[key] = s
        return s, True

    def siguiente_correlativo(self, empresa_id, tipo):
        s, _ = self.obtener_o_crear(empresa_id, tipo)
        s.correlativo_actual += 1
        return s, s.correlativo_actual

    def guardar(self, serie):
        key = (serie.empresa_id, serie.tipo)
        self._store[key] = serie


class MockClienteRepo:
    def __init__(self, cliente=None):
        self._cliente = cliente

    def obtener_por_id(self, cliente_id):
        if self._cliente and self._cliente.id == cliente_id:
            return self._cliente
        raise ClienteNoEncontrado(f"cliente {cliente_id}")

    def buscar(self, query="", solo_activos=True, limit=50):
        return [self._cliente] if self._cliente else []

    def guardar(self, cliente):
        return cliente

    def eliminar_soft(self, cliente_id, usuario_id=None):
        pass


class MockProductoRepo:
    def __init__(self, productos=None):
        self._productos = {p.id: p for p in (productos or [])}

    def obtener_por_id(self, producto_id):
        if producto_id not in self._productos:
            raise ProductoNoEncontrado(f"producto {producto_id}")
        return self._productos[producto_id]

    def buscar(self, query="", solo_activos=True, limit=50):
        return list(self._productos.values())

    def guardar(self, producto):
        return producto

    def eliminar_soft(self, producto_id, usuario_id=None):
        pass


class MockEmpresaRepo:
    def __init__(self, empresa=None):
        self._empresa = empresa

    def obtener_por_id(self, empresa_id):
        if self._empresa and self._empresa.id == empresa_id:
            return self._empresa
        raise EmpresaNoEncontrada(f"empresa {empresa_id}")

    def listar(self, solo_activos=True):
        return [self._empresa] if self._empresa else []

    def guardar(self, empresa):
        return empresa

    def eliminar_soft(self, empresa_id, usuario_id=None):
        pass


class MockLogSunatRepo:
    def __init__(self):
        self.logs = []

    def registrar(self, comprobante, **kwargs):
        self.logs.append({"comprobante_id": comprobante.id, **kwargs})

    def obtener_por_comprobante(self, comprobante_id):
        return []


class MockUnitOfWork:
    """UoW mockeable que entrega repos sincronizados."""

    def __init__(self, **repos):
        self._comprobantes = repos.get('comprobantes', MockComprobanteRepo())
        self._notas_credito = repos.get('notas_credito', MockNotaCreditoRepo())
        self._series = repos.get('series', MockSerieRepo())
        self._clientes = repos.get('clientes')
        self._productos = repos.get('productos')
        self._empresas = repos.get('empresas')
        self._logs = repos.get('logs_sunat', MockLogSunatRepo())

    def __enter__(self): return self
    def __exit__(self, *a): return None
    def commit(self): pass
    def rollback(self): pass

    @property
    def comprobantes(self): return self._comprobantes
    @property
    def notas_credito(self): return self._notas_credito
    @property
    def series(self): return self._series
    @property
    def clientes(self): return self._clientes
    @property
    def productos(self): return self._productos
    @property
    def empresas(self): return self._empresas
    @property
    def logs_sunat(self): return self._logs


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def empresa():
    return Empresa(id=1, ruc="20100000001", razon_social="Test SA")


@pytest.fixture
def cliente_ruc():
    return Cliente(
        id=1, tipo_doc="6", num_doc="20100000002",
        razon_social="Cliente RUC SA",
    )


@pytest.fixture
def cliente_dni():
    return Cliente(
        id=2, tipo_doc="1", num_doc="12345678",
        razon_social="Juan Perez",
    )


@pytest.fixture
def producto_gravado():
    return Producto(
        id=1, descripcion="Prod gravado",
        precio_unitario=Decimal("100"),
        afecto_igv=True,
    )


@pytest.fixture
def uow(empresa, cliente_ruc, producto_gravado):
    return MockUnitOfWork(
        comprobantes=MockComprobanteRepo(),
        notas_credito=MockNotaCreditoRepo(),
        series=MockSerieRepo(),
        clientes=MockClienteRepo(cliente=cliente_ruc),
        productos=MockProductoRepo(productos=[producto_gravado]),
        empresas=MockEmpresaRepo(empresa=empresa),
        logs_sunat=MockLogSunatRepo(),
    )


# ============================================================
# Tests ComprobanteService
# ============================================================

class TestComprobanteService:
    """Tests del ComprobanteService con mocks puros (sin BD)."""

    def test_crear_factura_con_ruc(self, uow, cliente_ruc):
        svc = ComprobanteService(uow)
        c = svc.crear(
            empresa_id=1,
            cliente_id=1,
            fecha=date.today(),
            tipo=TIPO_FACTURA,
            detalles_data=[{"producto_id": 1, "cantidad": "2"}],
        )
        assert c.estado == ESTADO_BORRADOR
        assert c.tipo == TIPO_FACTURA
        assert c.subtotal == Decimal("200")
        assert c.igv == Decimal("36")
        assert c.total == Decimal("236")
        assert c.numero == 1

    def test_factura_con_dni_acepta(self, uow, cliente_dni):
        """Factura con cliente DNI ahora se acepta (validacion flexible)."""
        uow._clientes = MockClienteRepo(cliente=cliente_dni)
        svc = ComprobanteService(uow)
        c = svc.crear(
            empresa_id=1, cliente_id=2, fecha=date.today(),
            tipo=TIPO_FACTURA,
            detalles_data=[{"producto_id": 1, "cantidad": 1}],
        )
        assert c.tipo == TIPO_FACTURA
        assert c.cliente_id == 2

    def test_validacion_longitud_dni_invalido(self, uow):
        """DNI con longitud incorrecta debe lanzar TipoDocumentoInvalido."""
        # Cliente mock con DNI invalido (bypass __post_init__ usando un
        # objeto que no es dataclass).
        class ClienteMockInvalido:
            id = 99
            tipo_doc = '1'
            num_doc = '12345'  # longitud invalida para DNI (debe ser 8)
            razon_social = 'TEST MALO'
        cliente_malo = ClienteMockInvalido()

        uow._clientes = MockClienteRepo(cliente=cliente_malo)
        svc = ComprobanteService(uow)
        with pytest.raises(TipoDocumentoInvalido):
            svc.crear(
                empresa_id=1, cliente_id=99, fecha=date.today(),
                tipo=TIPO_FACTURA,
                detalles_data=[{"producto_id": 1, "cantidad": 1}],
            )

    def test_boleta_con_dni_ok(self, uow, cliente_dni):
        uow._clientes = MockClienteRepo(cliente=cliente_dni)
        svc = ComprobanteService(uow)
        c = svc.crear(
            empresa_id=1, cliente_id=2, fecha=date.today(),
            tipo=TIPO_BOLETA,
            detalles_data=[{"producto_id": 1, "cantidad": 1}],
        )
        assert c.tipo == TIPO_BOLETA

    def test_numeracion_sin_saltos(self, uow):
        svc = ComprobanteService(uow)
        numeros = []
        for _ in range(3):
            c = svc.crear(
                empresa_id=1, cliente_id=1, fecha=date.today(),
                tipo=TIPO_FACTURA,
                detalles_data=[{"producto_id": 1, "cantidad": 1}],
            )
            numeros.append(c.numero)
        assert numeros == [1, 2, 3]

    def test_producto_no_existente_lanza_error(self, uow):
        svc = ComprobanteService(uow)
        with pytest.raises(ProductoNoEncontrado):
            svc.crear(
                empresa_id=1, cliente_id=1, fecha=date.today(),
                tipo=TIPO_FACTURA,
                detalles_data=[{"producto_id": 999, "cantidad": 1}],
            )

    def test_emitir_desde_borrador(self, uow):
        svc = ComprobanteService(uow)
        c = svc.crear(
            empresa_id=1, cliente_id=1, fecha=date.today(),
            tipo=TIPO_FACTURA,
            detalles_data=[{"producto_id": 1, "cantidad": 1}],
        )
        emitido = svc.emitir(c.id)
        assert emitido.estado == ESTADO_EMITIDO

    def test_emitir_desde_estado_invalido(self, uow):
        svc = ComprobanteService(uow)
        c = svc.crear(
            empresa_id=1, cliente_id=1, fecha=date.today(),
            tipo=TIPO_FACTURA,
            detalles_data=[{"producto_id": 1, "cantidad": 1}],
        )
        svc.emitir(c.id)
        with pytest.raises(EstadoInvalido):
            svc.emitir(c.id)  # ya emitido, no puede emitir otra vez

    def test_reenviar_solo_rechazado(self, uow):
        svc = ComprobanteService(uow)
        c = svc.crear(
            empresa_id=1, cliente_id=1, fecha=date.today(),
            tipo=TIPO_FACTURA,
            detalles_data=[{"producto_id": 1, "cantidad": 1}],
        )
        svc.emitir(c.id)
        with pytest.raises(EstadoInvalido):
            svc.reenviar(c.id)  # emitido no se reenvia

    def test_eliminar_aceptado_no_permitido(self, uow):
        svc = ComprobanteService(uow)
        c = svc.crear(
            empresa_id=1, cliente_id=1, fecha=date.today(),
            tipo=TIPO_FACTURA,
            detalles_data=[{"producto_id": 1, "cantidad": 1}],
        )
        svc.emitir(c.id)
        # Simular ACEPTADO
        c.estado = "ACEPTADO"
        uow.comprobantes.guardar(c)
        with pytest.raises(ComprobanteNoAnulable):
            svc.eliminar(c.id)

    def test_eliminar_borrador_ok(self, uow):
        svc = ComprobanteService(uow)
        c = svc.crear(
            empresa_id=1, cliente_id=1, fecha=date.today(),
            tipo=TIPO_FACTURA,
            detalles_data=[{"producto_id": 1, "cantidad": 1}],
        )
        svc.eliminar(c.id)
        rec = uow.comprobantes.obtener_por_id(c.id)
        assert not rec.activo


# ============================================================
# Tests NotaCreditoService
# ============================================================

class TestNotaCreditoService:
    """Tests del NotaCreditoService con mocks."""

    def test_emitir_nc_contra_comprobante_aceptado(self, uow):
        svc_comp = ComprobanteService(uow)
        c = svc_comp.crear(
            empresa_id=1, cliente_id=1, fecha=date.today(),
            tipo=TIPO_FACTURA,
            detalles_data=[{"producto_id": 1, "cantidad": 2}],
        )
        # Simular ACEPTADO manualmente
        c.estado = "ACEPTADO"
        c.total = Decimal("236")
        uow.comprobantes.guardar(c)

        svc_nc = NotaCreditoService(uow)
        nota = svc_nc.emitir(
            comprobante_referencia_id=c.id,
            tipo_nc="NC",
            tipo_nota="01",
            descripcion="Anulacion",
            monto_afectado=Decimal("100"),
        )
        assert nota.comprobante_referencia_id == c.id

    def test_nc_contra_borrador_lanza_error(self, uow):
        svc_comp = ComprobanteService(uow)
        c = svc_comp.crear(
            empresa_id=1, cliente_id=1, fecha=date.today(),
            tipo=TIPO_FACTURA,
            detalles_data=[{"producto_id": 1, "cantidad": 1}],
        )
        svc_nc = NotaCreditoService(uow)
        with pytest.raises(ComprobanteNoAceptado):
            svc_nc.emitir(
                comprobante_referencia_id=c.id,
                tipo_nc="NC",
                tipo_nota="01",
                descripcion="X",
            )

    def test_nc_monto_excedido(self, uow):
        svc_comp = ComprobanteService(uow)
        c = svc_comp.crear(
            empresa_id=1, cliente_id=1, fecha=date.today(),
            tipo=TIPO_FACTURA,
            detalles_data=[{"producto_id": 1, "cantidad": 1}],
        )
        c.estado = "ACEPTADO"
        c.total = Decimal("100")
        uow.comprobantes.guardar(c)
        svc_nc = NotaCreditoService(uow)
        with pytest.raises(MontoExcedidoError):
            svc_nc.emitir(
                comprobante_referencia_id=c.id,
                tipo_nc="NC",
                tipo_nota="01",
                descripcion="X",
                monto_afectado=Decimal("500"),
            )


class TestEventBus:
    """Tests del bus de eventos en memoria."""

    def test_subscribe_y_publish(self):
        from dominio.event_bus import InMemoryEventBus
        from dominio.eventos import ComprobanteCreado

        bus = InMemoryEventBus()
        recibidos = []

        def handler(event):
            recibidos.append(event)

        bus.subscribe(ComprobanteCreado, handler)
        evento = ComprobanteCreado(
            comprobante_id=1, empresa_id=1, tipo="01", numero=1,
            total=Decimal("100"),
        )
        bus.publish(evento)
        assert len(recibidos) == 1
        assert recibidos[0].comprobante_id == 1

    def test_unsubscribe(self):
        from dominio.event_bus import InMemoryEventBus
        from dominio.eventos import ComprobanteCreado

        bus = InMemoryEventBus()
        handler = lambda e: None
        bus.subscribe(ComprobanteCreado, handler)
        bus.unsubscribe(ComprobanteCreado, handler)
        assert len(bus._handlers[ComprobanteCreado]) == 0