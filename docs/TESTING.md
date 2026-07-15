# Estrategia de Testing

Este documento describe la estrategia de testing del proyecto y cómo ejecutarla.

## Estructura

```
tests/
├── dominio/             # Tests sin Django ni BD
├── infraestructura/     # Tests con BD SQLite
├── interfaces/          # Tests de la API REST (DRF APIClient)
└── apps/*/tests.py     # Tests legacy (compatibilidad)
```

## Cobertura objetivo

| Capa | Cobertura mínima | Estado actual |
|------|-----------------|---------------|
| Dominio (entidades) | 85% | ✅ |
| Dominio (servicios) | 60% | ✅ |
| Infraestructura | 70% | ✅ |
| Interfaces (API) | 60% | ✅ |
| **TOTAL** | **60%** | **≥60%** ✅ |

## Ejecución

```bash
# Activar venv
.venv\Scripts\activate

# Todos los tests
pytest

# Solo dominio (SIN Django, SIN BD)
pytest dominio/tests/ -p no:django

# Solo infraestructura
pytest infraestructura/tests/

# Solo interfaces
pytest interfaces/tests/

# Con cobertura
pytest --cov=dominio --cov=infraestructura --cov=interfaces --cov=apps --cov-report=term-missing

# Reporte HTML
pytest --cov --cov-report=html
# Abrir htmlcov/index.html
```

## Tipos de tests

### 1. Tests de dominio (Python puro)

No importan Django ni usan base de datos. Usan **mocks de los puertos** (repositorios).

```python
# dominio/tests/test_servicios.py
class TestComprobanteService:
    def test_crear_factura_con_ruc(self, uow, cliente_ruc):
        svc = ComprobanteService(uow)
        c = svc.crear(...)
        assert c.estado == ESTADO_BORRADOR
```

**Beneficios:**
- Rápidos (sin BD).
- Aislan la lógica de negocio.
- Sirven como documentación.

### 2. Tests de infraestructura

Verifican que los mappers y repositorios funcionan con la BD.

```python
# infraestructura/tests/test_persistencia.py
@pytest.mark.django_db
class TestDjangoComprobanteRepository:
    def test_guardar_y_obtener(self, ...):
        ent = Comprobante(...)
        saved = repo.guardar(ent)
        loaded = repo.obtener_por_id(saved.id)
        assert loaded.numero == num
```

### 3. Tests de interfaces (API)

Usan `APIClient` de DRF para simular HTTP requests.

```python
# interfaces/tests/test_api.py
@pytest.mark.django_db
class TestComprobanteAPI:
    def test_crear_factura_con_ruc(self, admin_user, empresa, ...):
        client = APIClient()
        client.force_authenticate(user=admin_user)
        response = client.post("/api/comprobantes/", {...})
        assert response.status_code == 201
```

## Buenas prácticas

1. **Un assert por test idealmente** (o relacionados).
2. **Nombres descriptivos**: `test_crear_factura_con_dni_lanza_tipo_doc_invalido`.
3. **Fixtures compartidos** en `conftest.py`.
4. **Tests de dominio sin mocks innecesarios** - solo lo necesario.
5. **No testear frameworks** - solo lógica de negocio.

## Convenciones

- Tests: prefijo `test_` obligatorio.
- Clases: prefijo `Test`.
- Mocks: prefijo `Mock` (ej. `MockComprobanteRepo`).
- Fixtures: nombres simples (`empresa`, `cliente`, etc.).

## CI/CD

Para integrar en CI (GitHub Actions, GitLab CI):

```yaml
- name: Tests
  run: |
    pip install -r requirements/local.txt
    pytest --cov --cov-report=xml
    
- name: Coverage report
  run: |
    coverage report --fail-under=60
```

## Debug

Para ver prints en tests:

```bash
pytest -s

# Solo un test
pytest -s dominio/tests/test_entidades.py::TestComprobanteEntidad::test_crear_basico
```
