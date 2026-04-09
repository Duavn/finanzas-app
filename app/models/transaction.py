"""
Modelo de Transacción (gasto o ingreso).
Almacena cada movimiento financiero del usuario.
"""

from datetime import datetime, date, timezone
from typing import Optional
from decimal import Decimal

from sqlalchemy import String, DateTime, Date, Numeric, ForeignKey, CheckConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Transaction(Base):
    __tablename__ = "transacciones"

    __table_args__ = (
        CheckConstraint("tipo IN ('gasto', 'ingreso')", name="ck_transaccion_tipo"),
        CheckConstraint("monto > 0", name="ck_transaccion_monto_positivo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    tipo: Mapped[str] = mapped_column(String(10), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    categoria_id: Mapped[int] = mapped_column(
        ForeignKey("categorias.id", ondelete="RESTRICT"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relación con categoría
    categoria: Mapped["Category"] = relationship(
        "Category", back_populates="transacciones", lazy="joined"
    )

    def __repr__(self) -> str:
        return (
            f"<Transaction id={self.id} tipo='{self.tipo}' "
            f"monto={self.monto} fecha={self.fecha}>"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "monto": float(self.monto),
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "tipo": self.tipo,
            "descripcion": self.descripcion,
            "categoria_id": self.categoria_id,
            "categoria_nombre": self.categoria.nombre if self.categoria else None,
            "categoria_color": self.categoria.color if self.categoria else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }