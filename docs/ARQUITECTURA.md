# Arquitectura Hexagonal

Este documento describe la arquitectura hexagonal estricta implementada en el proyecto de Facturación Electrónica SUNAT.

## Visión General

La arquitectura hexagonal (también llamada "Ports and Adapters") busca aislar la **lógica de negocio** del mundo exterior. Los principios fundamentales son:

1. El **dominio** (reglas de negocio) NO depende de frameworks.
2. La **infraestructura** (DB, API externas, UI) depende del dominio.
3. La comunicación es a través de **puertos** (interfaces) que el dominio define.
4. Los **adaptadores** implementan los puertos usando tecnología concreta.

## Diagrama de Capas

```
                          ┌─────────────────────┐
                          │   Mundo Exterior    │
                          │  (HTTP, SUNAT, DB)  │
                          └──────────┬──────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
       ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
       │  interfaces  │      │  interfaces  │      │infraestructura│
       │   (REST)     │      │   (web)      │      │  (adaptador)  │
       └──────┬───────┘      └──────┬───────┘      └──────┬───────┘
              │                     │                     │
              │      ┌──────────────▼─────────────┐       │
              └─────►│          dominio           │◄──────┘
                     │  (lógica de negocio puro)  │
                     └────────────────────────────┘
                              ▲      ▲
                              │      │
                     ┌────────┘      └────────┐
                     │                       │
              ┌──────┴────────┐      ┌───────┴───────┐
              │   entidades   │      │   servicios   │
              │  (dataclass)  │      │  (casos uso)  │
              └───────────────┘      └───────────────┘
```

## Capas del Proyecto

### 1. Dominio (`dominio/`)

**Propósito:** Lógica de negocio pura en Python.

**NO contiene:**
- `import django`
- `from apps.*`
- Acceso directo a la BD
- Cualquier framework

**Contiene:**

```
dominio/
├── entidades/
│   ├── comprobante.py       # @dataclass Comprobante + lógica de transiciones
│   ├── nota_credito.py      # @dataclass NotaCredito + validación
│   ├── cliente.py           # @dataclass Cliente + validación RUC/DNI
│   ├── producto.py          # @dataclass Producto + validación
│   └── empresa.py           # @dataclass Empresa
├── servicios/
│   ├── comprobante_service.py  # ComprobanteService.crear(), .emitir(), etc.
│   ├── nota_credito_service.py # NotaCreditoService.emitir(), .eliminar()
│   ├── numeracion_service.py   # NumeracionService.siguiente_correlativo()
│   ├── cliente_service.py
│   ├── producto_service.py
│   └── sunat_service.py        # SunatEnvioService.enviar_comprobante()
├── puertos/
│   ├── repositorios.py     # Protocol IComprobanteRepository, etc.
│   └── sunat.py            # Protocol IOSEService, IXmlSigner
├── excepciones.py          # DomainError + jerarquía
├── eventos.py              # @dataclass(frozen=True) para eventos
└── event_bus.py            # Bus de eventos en memoria
```

**Ejemplo de entidad:**

```python
# dominio/entidades/comprobante.py - SIN imports de Django
from dataclasses import dataclass
from decimal import Decimal
from ..excepciones import EstadoInvalido

@dataclass
class Comprobante:
    id: int | None
    empresa_id: int
    cliente_id: int
    tipo: str
    estado: str = "BORRADOR"
    # ...
    
    TRANSICIONES_VALIDAS = {
        "BORRADOR": ["EMITIDO"],
        "EMITIDO": ["ENVIADO", "BORRADOR"],
        "ENVIADO": ["ACEPTADO", "RECHAZADO"],
        "ACEPTADO": ["ANULADO_PARCIAL", "ANULADO_TOTAL"],
    }
    
    def cambiar_estado(self, nuevo: str) -> None:
        permitidas = self.TRANSICIONES_VALIDAS.get(self.estado, [])
        if nuevo not in permitidas:
            raise EstadoInvalido(...)
        self.estado = nuevo
```

**Ejemplo de servicio (caso de uso):**

```python
# dominio/servicios/comprobante_service.py
class ComprobanteService:
    def __init__(self, uow: IUnitOfWork, event_bus=None, tasa_igv=Decimal("0.18")):
        self._uow = uow
        self._events = event_bus
        self._tasa_igv = tasa_igv
    
    def crear(self, empresa_id, cliente_id, fecha, tipo, detalles_data, creado_por_id=None):
        # 1. Validar empresa
        empresa = self._uow.empresas.obtener_por_id(empresa_id)
        # 2. Validar cliente
        cliente = self._uow.clientes.obtener_por_id(cliente_id)
        # 3. Validar reglas tributarias
        self._validar_tipo_documento(tipo, cliente)
        # 4. Obtener numeracion
        serie, numero = self._uow.series.siguiente_correlativo(empresa_id, tipo)
        # 5. Construir entidad
        comprobante = Comprobante(...)
        comprobante.calcular_totales(self._tasa_igv)
        # 6. Persistir
        with self._uow:
            guardado = self._uow.comprobantes.guardar(comprobante)
            self._uow.commit()
        # 7. Publicar evento
        if self._events:
            self._events.publish(ComprobanteCreado(...))
        return guardado
```

### 2. Infraestructura (`infraestructura/`)

**Propósito:** Adaptadores concretos que conectan el dominio con el mundo real.

```
infraestructura/
├── persistencia/
│   ├── mappers.py       # Convierte Modelo Django <-> Entidad dominio
│   ├── repos.py         # DjangoComprobanteRepository, etc.
│   └── unit_of_work.py  # DjangoUnitOfWork (transacciones)
└── sunat/
    ├── mock_ose.py      # MockOSEAdapter para desarrollo
    ├── real_ose.py      # RealOSEAdapter con zeep
    ├── factory.py       # get_ose_client(), get_sunat_envio_service()
    ├── signer_adapter.py
    ├── xml_generator_adapter.py
    └── zip_helper.py
```

**Mappers:** Funciones puras `modelo_a_entidad()` y `entidad_a_modelo()`.

**Repositorios:** Implementan los `Protocol` del dominio usando Django ORM.

**UnitOfWork:** Implementa `IUnitOfWork` con `transaction.atomic()`.

### 3. Interfaces (`interfaces/`)

**Propósito:** Adaptadores de entrada (API REST, web).

```
interfaces/
├── api/
│   ├── comprobante_views.py   # ViewSets delgados
│   ├── nota_credito_views.py
│   ├── cliente_views.py
│   ├── producto_views.py
│   ├── serializers.py
│   ├── exception_handler.py   # DomainError -> HTTP 400/404/422
│   ├── health.py              # /api/health/
│   └── urls.py
├── container.py               # Inyección de dependencias
└── ...
```

**View delgada:**

```python
# interfaces/api/comprobante_views.py
class ComprobanteViewSet(viewsets.ModelViewSet):
    def create(self, request, *args, **kwargs):
        # 1. Validar entrada con serializer
        data = self.get_serializer(data=request.data).validated_data
        # 2. Llamar al servicio de dominio
        service = get_comprobante_service()
        comp = service.crear(...)
        # 3. Retornar respuesta
        return Response(...)
```

### 4. Apps Django (`apps/`)

**Propósito:** Shell de Django. Modelos ORM, admin, migraciones, URLs legacy.

```
apps/
├── comprobantes/
│   ├── models.py          # Modelos ORM (ModeloBase + Comprobante, etc.)
│   ├── admin.py
│   ├── migrations/
│   ├── services.py        # ★ Backward-compat wrapper
│   ├── repositories.py    # ★ Backward-compat wrapper
│   ├── api_views.py       # ★ Backward-compat wrapper
│   ├── serializers.py     # ★ Backward-compat wrapper
│   └── views.py           # Templates web
└── ...
```

**Backwards-compat:** Los archivos `services.py`, `repositories.py`, etc. en `apps/` son **wrappers** que delegan a la nueva capa hexagonal. Esto preserva la compatibilidad con código viejo.

## Inyección de Dependencias

El `interfaces/container.py` es el único lugar donde se hace wiring:

```python
# interfaces/container.py
def get_comprobante_service() -> ComprobanteService:
    return ComprobanteService(
        uow=get_uow(),
        event_bus=event_bus,
    )

def get_uow() -> DjangoUnitOfWork:
    return DjangoUnitOfWork()
```

Las views obtienen el servicio vía `get_comprobante_service()`. No instancian repositorios directamente.

## Mapeo Excepciones → HTTP

`interfaces/api/exception_handler.py` traduce:

| Excepción dominio | HTTP |
|-------------------|------|
| `TipoDocumentoInvalido` | 400 |
| `EstadoInvalido` | 400 |
| `ComprobanteNoAnulable` | 422 |
| `ComprobanteNoAceptado` | 422 |
| `MontoExcedidoError` | 422 |
| `ReglaNegocioViolada` | 422 |
| `RecursoNoEncontrado` | 404 |
| `AccesoNoAutorizado` | 403 |
| `FirmaDigitalInvalida` | 500 |
| `EnvioSunatFallido` | 502 |
| `DomainError` (genérica) | 400 |

Configurado en `settings/base.py`:
```python
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'interfaces.api.exception_handler.domain_exception_handler',
    ...
}
```

## Testing

- **Tests de dominio:** `dominio/tests/` - Sin Django, sin BD. Usan mocks de los repositorios.
- **Tests de infraestructura:** `infraestructura/tests/` - Con BD SQLite, prueban mappers y repos.
- **Tests de interfaces:** `interfaces/tests/` - DRF APIClient, prueban HTTP endpoints.
- **Tests de apps:** `apps/*/tests.py` - Tests legacy (compat).

```bash
# Solo dominio (sin BD, sin Django)
pytest dominio/tests/ -p no:django

# Todo
pytest
```

## Migración desde la versión anterior

La migración fue **no destructiva**:

1. Se creó la nueva estructura `dominio/`, `infraestructura/`, `interfaces/`.
2. Los archivos originales en `apps/*/` se convirtieron en wrappers que re-exportan.
3. Las URLs en `config/urls.py` apuntan ahora a `interfaces.api.urls` y a los wrappers de `apps/*/urls.py`.

Para usar la nueva arquitectura en código nuevo:

```python
# ✓ NUEVO: usar el container
from interfaces.container import get_comprobante_service
service = get_comprobante_service()
comprobante = service.crear(...)

# ✓ NUEVO: usar las views de interfaces
from interfaces.api.comprobante_views import ComprobanteViewSet

# ⚠️ LEGACY: aún funciona
from apps.comprobantes.services import ComprobanteService
comprobante = ComprobanteService.crear(data, usuario=request.user)
```

## Reglas de oro

1. **Dominio no importa Django.** Si lo hace, es un bug.
2. **Views no tocan ORM directamente.** Solo llaman al servicio.
3. **Servicios reciben dependencias por constructor.** No hacen `from apps...`.
4. **Mappers son funciones puras.** `modelo_a_entidad()` y `entidad_a_modelo()`.
5. **Tests de dominio sin BD.** Si un test de dominio necesita BD, está mal.
