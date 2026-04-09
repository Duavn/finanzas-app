"""
Tests básicos de la capa de servicios.
Ejecutar con: python -m pytest tests/ -v
Usa una DB SQLite en memoria para no afectar datos reales.
"""

import pytest
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
import app.models.category    # noqa
import app.models.transaction  # noqa
import app.models.investment   # noqa

from app.services.category_service import CategoryService
from app.services.transaction_service import TransactionService
from app.services.investment_service import InvestmentService


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def session():
    """Sesión en memoria, se descarta al terminar cada test."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def cat_service(session):
    return CategoryService(session)


@pytest.fixture
def tx_service(session):
    return TransactionService(session)


@pytest.fixture
def inv_service(session):
    return InvestmentService(session)


@pytest.fixture
def categoria_gasto(cat_service):
    return cat_service.create("Alimentación", "gasto", "#E74C3C")


@pytest.fixture
def categoria_ingreso(cat_service):
    return cat_service.create("Salario", "ingreso", "#2ECC71")


# ── Tests: CategoryService ────────────────────────────────────────────────────

class TestCategoryService:
    def test_create_gasto(self, cat_service):
        cat = cat_service.create("Transporte", "gasto")
        assert cat.id is not None
        assert cat.nombre == "Transporte"
        assert cat.tipo == "gasto"

    def test_create_ingreso(self, cat_service):
        cat = cat_service.create("Freelance", "ingreso", "#1ABC9C")
        assert cat.tipo == "ingreso"
        assert cat.color == "#1ABC9C"

    def test_create_duplicate_raises(self, cat_service):
        cat_service.create("Ropa", "gasto")
        with pytest.raises(ValueError, match="Ya existe"):
            cat_service.create("Ropa", "gasto")

    def test_create_tipo_invalido(self, cat_service):
        with pytest.raises(ValueError, match="tipo"):
            cat_service.create("Test", "invalido")

    def test_get_all(self, cat_service):
        cat_service.create("A", "gasto")
        cat_service.create("B", "ingreso")
        cats = cat_service.get_all()
        assert len(cats) == 2

    def test_get_by_tipo(self, cat_service):
        cat_service.create("Comida", "gasto")
        cat_service.create("Sueldo", "ingreso")
        gastos = cat_service.get_by_tipo("gasto")
        assert len(gastos) == 1
        assert gastos[0].nombre == "Comida"

    def test_update(self, cat_service, categoria_gasto):
        updated = cat_service.update(categoria_gasto.id, nombre="Comida", color="#FF0000")
        assert updated.nombre == "Comida"
        assert updated.color == "#FF0000"

    def test_delete_sin_transacciones(self, cat_service):
        cat = cat_service.create("Temporal", "gasto")
        cat_service.delete(cat.id)
        assert cat_service.get_by_id(cat.id) is None

    def test_delete_con_transacciones_raises(self, session, cat_service, tx_service, categoria_gasto):
        tx_service.create(50000, date.today(), "gasto", categoria_gasto.id)
        with pytest.raises(ValueError, match="transacción"):
            cat_service.delete(categoria_gasto.id)


# ── Tests: TransactionService ─────────────────────────────────────────────────

class TestTransactionService:
    def test_create_gasto(self, tx_service, categoria_gasto):
        tx = tx_service.create(100_000, date.today(), "gasto", categoria_gasto.id)
        assert tx.id is not None
        assert float(tx.monto) == 100_000.0
        assert tx.tipo == "gasto"

    def test_create_ingreso(self, tx_service, categoria_ingreso):
        tx = tx_service.create(3_000_000, date.today(), "ingreso", categoria_ingreso.id, "Sueldo")
        assert tx.tipo == "ingreso"
        assert tx.descripcion == "Sueldo"

    def test_monto_negativo_raises(self, tx_service, categoria_gasto):
        with pytest.raises(ValueError, match="mayor a 0"):
            tx_service.create(-500, date.today(), "gasto", categoria_gasto.id)

    def test_fecha_futura_raises(self, tx_service, categoria_gasto):
        from datetime import timedelta
        with pytest.raises(ValueError, match="futura"):
            tx_service.create(1000, date.today() + timedelta(days=1), "gasto", categoria_gasto.id)

    def test_tipo_no_coincide_categoria(self, tx_service, categoria_gasto):
        """No se puede crear un ingreso en una categoría de gasto."""
        with pytest.raises(ValueError, match="tipo"):
            tx_service.create(1000, date.today(), "ingreso", categoria_gasto.id)

    def test_get_all_filtrado(self, tx_service, categoria_gasto, categoria_ingreso):
        tx_service.create(50_000, date(2024, 1, 15), "gasto", categoria_gasto.id)
        tx_service.create(3_000_000, date(2024, 1, 15), "ingreso", categoria_ingreso.id)
        gastos = tx_service.get_all(tipo="gasto")
        assert len(gastos) == 1

    def test_get_totales(self, tx_service, categoria_gasto, categoria_ingreso):
        tx_service.create(1_000_000, date.today(), "ingreso", categoria_ingreso.id)
        tx_service.create(300_000, date.today(), "gasto", categoria_gasto.id)
        totales = tx_service.get_totales()
        assert totales["ingreso"] == 1_000_000.0
        assert totales["gasto"]   == 300_000.0
        assert totales["balance"] == 700_000.0

    def test_delete(self, tx_service, categoria_gasto):
        tx = tx_service.create(20_000, date.today(), "gasto", categoria_gasto.id)
        tx_service.delete(tx.id)
        assert tx_service.get_by_id(tx.id) is None

    def test_gastos_por_categoria(self, tx_service, cat_service, categoria_gasto):
        cat2 = cat_service.create("Transporte", "gasto", "#E67E22")
        tx_service.create(100_000, date.today(), "gasto", categoria_gasto.id)
        tx_service.create(50_000, date.today(), "gasto", cat2.id)
        result = tx_service.get_gastos_por_categoria()
        assert len(result) == 2
        assert result[0]["total"] >= result[1]["total"]  # ordenado desc


# ── Tests: InvestmentService ──────────────────────────────────────────────────

class TestInvestmentService:
    def test_create(self, inv_service):
        inv = inv_service.create(
            nombre="Fondo emergencia",
            tipo="ahorro",
            monto_inicial=5_000_000,
            fecha_inicio=date.today(),
        )
        assert inv.id is not None
        assert float(inv.monto_actual) == 5_000_000.0  # igual al inicial por defecto

    def test_rendimiento_positivo(self, inv_service):
        inv = inv_service.create("ETF", "acciones", 1_000_000, date.today(), monto_actual=1_200_000)
        assert inv.rendimiento == pytest.approx(20.0)
        assert inv.ganancia == pytest.approx(200_000.0)

    def test_rendimiento_negativo(self, inv_service):
        inv = inv_service.create("Cripto", "cripto", 1_000_000, date.today(), monto_actual=800_000)
        assert inv.rendimiento == pytest.approx(-20.0)

    def test_update_valor(self, inv_service):
        inv = inv_service.create("CDT", "bonos", 2_000_000, date.today())
        updated = inv_service.update_valor(inv.id, 2_200_000)
        assert float(updated.monto_actual) == 2_200_000.0

    def test_resumen_portafolio(self, inv_service):
        inv_service.create("A", "ahorro", 1_000_000, date.today(), monto_actual=1_100_000)
        inv_service.create("B", "acciones", 2_000_000, date.today(), monto_actual=1_800_000)
        resumen = inv_service.get_resumen()
        assert resumen["cantidad"] == 2
        assert resumen["total_inicial"] == 3_000_000.0
        assert resumen["total_actual"] == 2_900_000.0

    def test_delete(self, inv_service):
        inv = inv_service.create("Temporal", "ahorro", 100_000, date.today())
        inv_service.delete(inv.id)
        assert inv_service.get_by_id(inv.id) is None


# ── Tests: Validators ─────────────────────────────────────────────────────────

class TestValidators:
    def test_validate_monto_valido(self):
        from app.utils.validators import validate_monto
        ok, val, _ = validate_monto("150000")
        assert ok and val == 150000.0

    def test_validate_monto_coma(self):
        from app.utils.validators import validate_monto
        ok, val, _ = validate_monto("1,500.50")
        assert ok and val == 1500.50

    def test_validate_monto_negativo(self):
        from app.utils.validators import validate_monto
        ok, _, msg = validate_monto("-100")
        assert not ok and "mayor" in msg

    def test_validate_fecha_valida(self):
        from app.utils.validators import validate_fecha
        ok, fecha, _ = validate_fecha("01/01/2024")
        assert ok and fecha.year == 2024

    def test_validate_fecha_formato_iso(self):
        from app.utils.validators import validate_fecha
        ok, fecha, _ = validate_fecha("2024-06-15")
        assert ok and fecha.month == 6

    def test_validate_fecha_futura(self):
        from app.utils.validators import validate_fecha
        from datetime import timedelta
        futura = (date.today() + timedelta(days=5)).strftime("%d/%m/%Y")
        ok, _, msg = validate_fecha(futura)
        assert not ok and "futura" in msg

    def test_validate_color_valido(self):
        from app.utils.validators import validate_color_hex
        ok, color, _ = validate_color_hex("#4A90D9")
        assert ok and color == "#4A90D9"

    def test_validate_color_invalido(self):
        from app.utils.validators import validate_color_hex
        ok, _, msg = validate_color_hex("rojo")
        assert not ok
