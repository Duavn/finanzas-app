"""
Base declarativa compartida por todos los modelos SQLAlchemy.
Centralizar aquí evita importaciones circulares.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Clase base para todos los modelos ORM."""
    pass