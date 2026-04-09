
"""
Servicio de categorías.
Encapsula toda la lógica de negocio relacionada con categorías.
No depende de la capa de vistas — testeable de forma independiente.
"""

from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.category import Category
from app.database.connection import get_session


class CategoryService:
    """CRUD y consultas de categorías."""

    # Colores por defecto para nuevas categorías (rotación cíclica)
    DEFAULT_COLORS = [
        "#4A90D9", "#E74C3C", "#2ECC71", "#F39C12", "#9B59B6",
        "#1ABC9C", "#E67E22", "#3498DB", "#E91E63", "#00BCD4",
    ]

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

    # ── Creación ────────────────────────────────────────────────────────────

    def create(self, nombre: str, tipo: str, color: Optional[str] = None) -> Category:
        """
        Crea una nueva categoría.
        Raises ValueError si el nombre ya existe o el tipo es inválido.
        """
        nombre = nombre.strip()
        if not nombre:
            raise ValueError("El nombre de la categoría no puede estar vacío.")
        if tipo not in ("gasto", "ingreso"):
            raise ValueError("El tipo debe ser 'gasto' o 'ingreso'.")

        if color is None:
            # Cambia esta línea en create():
            count = len(self.get_all())
            color = self.DEFAULT_COLORS[count % len(self.DEFAULT_COLORS)]

        category = Category(nombre=nombre, tipo=tipo, color=color)
        try:
            self.session.add(category)
            self.session.commit()
            return category
        except IntegrityError:
            self.session.rollback()
            raise ValueError(f"Ya existe una categoría con el nombre '{nombre}'.")
    # ── Lectura ──────────────────────────────────────────────────────────────

    def get_all(self) -> List[Category]:
        """Retorna todas las categorías ordenadas por nombre."""
        return (
            self.session.query(Category)
            .order_by(Category.tipo, Category.nombre)
            .all()
        )

    def get_by_tipo(self, tipo: str) -> List[Category]:
        """Filtra categorías por tipo ('gasto' o 'ingreso')."""
        return (
            self.session.query(Category)
            .filter(Category.tipo == tipo)
            .order_by(Category.nombre)
            .all()
        )

    def get_by_id(self, category_id: int) -> Optional[Category]:
        return self.session.query(Category).filter(Category.id == category_id).first()

    # ── Actualización ────────────────────────────────────────────────────────

    def update(
        self,
        category_id: int,
        nombre: Optional[str] = None,
        tipo: Optional[str] = None,
        color: Optional[str] = None,
    ) -> Category:
        """Actualiza los campos indicados de una categoría."""
        category = self.get_by_id(category_id)
        if not category:
            raise ValueError(f"Categoría con id={category_id} no encontrada.")

        if nombre is not None:
            nombre = nombre.strip()
            if not nombre:
                raise ValueError("El nombre no puede estar vacío.")
            category.nombre = nombre
        if tipo is not None:
            if tipo not in ("gasto", "ingreso"):
                raise ValueError("El tipo debe ser 'gasto' o 'ingreso'.")
            category.tipo = tipo
        if color is not None:
            category.color = color

        try:
            self.session.commit()
            return category
        except IntegrityError:
            self.session.rollback()
            raise ValueError(f"Ya existe una categoría con ese nombre.")
    # ── Eliminación ──────────────────────────────────────────────────────────

    def delete(self, category_id: int) -> None:
        """
        Elimina una categoría.
        Raises ValueError si tiene transacciones asociadas.
        """
        category = self.get_by_id(category_id)
        if not category:
            raise ValueError(f"Categoría con id={category_id} no encontrada.")

        # Cambia esto en delete():
        if len(category.transacciones) > 0:
            raise ValueError(
                f"No se puede eliminar '{category.nombre}' porque tiene "
                f"{len(category.transacciones)} transacción(es) asociada(s)."
            )

        self.session.delete(category)
        self.session.commit()