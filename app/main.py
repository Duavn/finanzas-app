"""
Punto de entrada de la aplicación Finanzas Personales.
Inicializa la base de datos y lanza la ventana principal.
"""

import sys
from pathlib import Path

# Asegurar que el directorio raíz del proyecto esté en el path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database.connection import init_db
from app.views.main_window import MainWindow


def main():
    """Función principal: inicializa la DB y arranca la UI."""
    # Crear tablas si no existen
    init_db()

    # Lanzar ventana principal
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
