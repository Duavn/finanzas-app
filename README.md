# 💰 Finanzas Personales

App de escritorio local para gestión de finanzas personales. Construida con Python + CustomTkinter + SQLite.

---

## Requisitos

- Python 3.10 o superior
- pip

---

## Instalación (VSCode)

```bash
# 1. Clonar / abrir la carpeta del proyecto en VSCode

# 2. Crear entorno virtual (recomendado)
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. (Opcional) Poblar con datos de prueba
python seed_data.py

# 5. Ejecutar la aplicación
python app/main.py
```

---

## Estructura del proyecto

```
finanzas_app/
├── app/
│   ├── main.py                  # Punto de entrada
│   ├── models/                  # ORM SQLAlchemy
│   │   ├── category.py          # Modelo Categoría
│   │   ├── transaction.py       # Modelo Transacción
│   │   └── investment.py        # Modelo Inversión
│   ├── services/                # Lógica de negocio
│   │   ├── category_service.py
│   │   ├── transaction_service.py
│   │   └── investment_service.py
│   ├── views/                   # UI CustomTkinter
│   │   ├── main_window.py       # Ventana + navegación
│   │   ├── dashboard_view.py    # Resumen + gráficos
│   │   ├── transaction_view.py  # CRUD transacciones
│   │   ├── category_view.py     # CRUD categorías
│   │   ├── stats_view.py        # Estadísticas
│   │   └── investment_view.py   # Portafolio
│   ├── database/
│   │   └── connection.py        # Engine + Session SQLAlchemy
│   └── utils/
│       ├── charts.py            # Funciones Matplotlib
│       └── validators.py        # Validación de inputs
├── data/
│   └── finanzas.db              # SQLite (generado automáticamente)
├── tests/
│   └── test_services.py
├── seed_data.py
├── requirements.txt
└── README.md
```

---

## Ejecutar tests

```bash
pip install pytest
python -m pytest tests/ -v
```

---

## Pantallas disponibles

| Pantalla | Descripción |
|---|---|
| 🏠 Dashboard | Resumen financiero, tarjetas KPI y gráficos del período seleccionado |
| 💳 Transacciones | Registro, edición y filtrado de gastos e ingresos |
| 🏷️ Categorías | CRUD de categorías con selector de color |
| 📊 Estadísticas | Análisis detallado con filtros de fecha personalizados |
| 📈 Inversiones | Portafolio de ahorros e inversiones con rendimiento |

---

## Decisiones técnicas

| Decisión | Justificación |
|---|---|
| **CustomTkinter** | UI moderna sobre Tkinter nativo, sin dependencias de sistema, tema oscuro incluido |
| **SQLAlchemy ORM** | Abstracción de DB que facilita futura migración a PostgreSQL/MySQL |
| **SQLite** | Cero configuración, archivo portátil, ideal para uso personal local |
| **Matplotlib embebido** | Se integra nativamente con Tkinter mediante FigureCanvasTkAgg |
| **Service Layer** | Desacopla la lógica de negocio de la UI, permite testing sin levantar ventanas |
| **Patrón MVC adaptado** | Modelos (SQLAlchemy) + Servicios (lógica) + Vistas (CustomTkinter) |
