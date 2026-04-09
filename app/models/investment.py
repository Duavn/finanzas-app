"""
Modelo de Inversión/Ahorro.
Registra instrumentos de ahorro e inversión simples sin APIs externas.
"""

from datetime import datetime, date, timezone
from typing import Optional
from decimal import Decimal

from sqlalchemy import String, DateTime, Date, Numeric, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Investment(Base):
    __tablename__ = "inversiones"

    __table_args__ = (
        CheckConstraint("monto_inicial >= 0", name="ck_inversion_monto_inicial"),
        CheckConstraint("monto_actual >= 0", name="ck_inversion_monto_actual"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)

    monto_inicial: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    monto_actual: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    notas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    @property
    def rendimiento(self) -> float:
        """Retorna el rendimiento porcentual."""
        if self.monto_inicial == 0:
            return 0.0
        return float(
            ((self.monto_actual - self.monto_inicial) / self.monto_inicial) * 100
        )

    @property
    def ganancia(self) -> float:
        """Ganancia/pérdida absoluta."""
        return float(self.monto_actual - self.monto_inicial)

    def __repr__(self) -> str:
        return f"<Investment id={self.id} nombre='{self.nombre}' monto_actual={self.monto_actual}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "tipo": self.tipo,
            "monto_inicial": float(self.monto_inicial),
            "monto_actual": float(self.monto_actual),
            "rendimiento": self.rendimiento,
            "ganancia": self.ganancia,
            "fecha_inicio": self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            "notas": self.notas,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }