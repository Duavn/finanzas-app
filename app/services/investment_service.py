"""
Servicio de inversiones y ahorros.
Gestiona el ciclo de vida de instrumentos de inversión.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict

from sqlalchemy.orm import Session

from app.models.investment import Investment
from app.database.connection import get_session


class InvestmentService:
    """CRUD de inversiones con cálculo de rendimiento."""

    TIPOS_VALIDOS = ["ahorro", "acciones", "bonos", "cripto", "fondo", "inmueble", "otro"]

    def __init__(self, session: Optional[Session] = None):
        self._session = session
        self._owns_session = session is None

    @property
    def session(self) -> Session:
        if self._session is None:
            self._session = get_session()
        return self._session

    def close(self):
        if self._owns_session and self._session:
            self._session.close()
            self._session = None

    # ── Creación ─────────────────────────────────────────────────────────────

    def create(
        self,
        nombre: str,
        tipo: str,
        monto_inicial: float,
        fecha_inicio: date,
        monto_actual: Optional[float] = None,
        notas: Optional[str] = None,
    ) -> Investment:
        nombre = nombre.strip()
        if not nombre:
            raise ValueError("El nombre no puede estar vacío.")

        if tipo not in self.TIPOS_VALIDOS:
            raise ValueError(f"Tipo inválido. Usa: {self.TIPOS_VALIDOS}")

        if float(monto_inicial) < 0:
            raise ValueError("El monto inicial no puede ser negativo.")

        monto_inicial = Decimal(monto_inicial)
        monto_actual = Decimal(monto_actual if monto_actual is not None else monto_inicial)

        inv = Investment(
            nombre=nombre,
            tipo=tipo,
            monto_inicial=monto_inicial,
            monto_actual=monto_actual,
            fecha_inicio=fecha_inicio,
            notas=notas.strip() if notas else None,
            updated_at=datetime.now(timezone.utc),
        )

        self.session.add(inv)
        self.session.commit()
        return inv

    # ── Lectura ──────────────────────────────────────────────────────────────

    def get_all(self) -> List[Investment]:
        return (
            self.session.query(Investment)
            .order_by(Investment.fecha_inicio.desc())
            .all()
        )

    def get_by_id(self, inv_id: int) -> Optional[Investment]:
        return self.session.query(Investment).filter(Investment.id == inv_id).first()

    # ── Actualización de valor ────────────────────────────────────────────────

    def update_valor(self, inv_id: int, nuevo_monto: float) -> Investment:
        inv = self.get_by_id(inv_id)
        if not inv:
            raise ValueError(f"Inversión con id={inv_id} no encontrada.")

        if float(nuevo_monto) < 0:
            raise ValueError("El monto actual no puede ser negativo.")

        inv.monto_actual = Decimal(nuevo_monto)
        inv.updated_at = datetime.now(timezone.utc)

        self.session.commit()
        return inv

    # ── Actualización completa ────────────────────────────────────────────────

    def update(
        self,
        inv_id: int,
        nombre: Optional[str] = None,
        tipo: Optional[str] = None,
        monto_inicial: Optional[float] = None,
        monto_actual: Optional[float] = None,
        fecha_inicio: Optional[date] = None,
        notas: Optional[str] = None,
    ) -> Investment:
        inv = self.get_by_id(inv_id)
        if not inv:
            raise ValueError(f"Inversión con id={inv_id} no encontrada.")

        if nombre is not None:
            inv.nombre = nombre.strip()

        if tipo is not None:
            if tipo not in self.TIPOS_VALIDOS:
                raise ValueError(f"Tipo inválido. Usa: {self.TIPOS_VALIDOS}")
            inv.tipo = tipo

        if monto_inicial is not None:
            inv.monto_inicial = Decimal(monto_inicial)

        if monto_actual is not None:
            inv.monto_actual = Decimal(monto_actual)

        if fecha_inicio is not None:
            inv.fecha_inicio = fecha_inicio

        if notas is not None:
            inv.notas = notas.strip() or None

        inv.updated_at = datetime.now(timezone.utc)

        self.session.commit()
        return inv

    # ── Eliminación ──────────────────────────────────────────────────────────

    def delete(self, inv_id: int) -> None:
        inv = self.get_by_id(inv_id)
        if not inv:
            raise ValueError(f"Inversión con id={inv_id} no encontrada.")

        self.session.delete(inv)
        self.session.commit()

    # ── Resumen ──────────────────────────────────────────────────────────────

    def get_resumen(self) -> Dict:
        inversiones = self.get_all()

        total_inicial = sum(float(i.monto_inicial) for i in inversiones)
        total_actual = sum(float(i.monto_actual) for i in inversiones)

        ganancia_total = total_actual - total_inicial
        rendimiento = (ganancia_total / total_inicial * 100) if total_inicial > 0 else 0.0

        return {
            "cantidad": len(inversiones),
            "total_inicial": total_inicial,
            "total_actual": total_actual,
            "ganancia_total": ganancia_total,
            "rendimiento_porcentaje": rendimiento,
        }