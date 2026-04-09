"""
Modelo de Categoría.
Las categorías clasifican transacciones en tipos (gastos/ingresos).
"""

from datetime import datetime, timezone
from typing import List

from sqlalchemy import String, DateTime, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Category(Base):
    __tablename__ = "categorias"

    __table_args__ = (
        CheckConstraint("tipo IN ('gasto', 'ingreso')", name="ck_categoria_tipo"),
        UniqueConstraint("nombre", "tipo", name="uq_categoria_nombre_tipo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo: Mapped[str] = mapped_column(String(10), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#4A90D9")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relación con transacciones
    transacciones: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        back_populates="categoria",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Category id={self.id} nombre='{self.nombre}' tipo='{self.tipo}'>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "tipo": self.tipo,
            "color": self.color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }