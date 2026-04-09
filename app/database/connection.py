from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path

from app.models.base import Base

# Ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "finanzas.db"

# Crear carpeta data si no existe
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Engine SQLite
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

# Sesión
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Crea las tablas en la base de datos."""
    from app.models import category, transaction, investment
    Base.metadata.create_all(bind=engine)


def get_session():
    """Retorna una sesión de base de datos."""
    return SessionLocal()