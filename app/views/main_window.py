"""
Ventana principal de la aplicación.
Implementa el layout base con sidebar de navegación y área de contenido.
Actúa como controlador de navegación entre vistas.
"""

import customtkinter as ctk
from typing import Dict, Type

from app.database.connection import get_session


# Configuración global del tema
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Constantes de diseño
SIDEBAR_WIDTH = 200
BG_COLOR = "#1a1a2e"
SIDEBAR_COLOR = "#16213e"
ACCENT_COLOR = "#0f3460"
HIGHLIGHT_COLOR = "#e94560"
TEXT_PRIMARY = "#e0e0e0"
TEXT_SECONDARY = "#a0a0b0"


class MainWindow(ctk.CTk):
    """
    Ventana raíz de la aplicación.
    Gestiona la navegación entre vistas mediante un sidebar lateral.
    """

    def __init__(self):
        super().__init__()

        # ── Configuración de ventana ──────────────────────────────────────
        self.title("💰 Finanzas Personales")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(fg_color=BG_COLOR)

        # Sesión compartida entre servicios de la sesión actual
        self._session = get_session()

        # ── Layout principal (sidebar + contenido) ────────────────────────
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_content_area()

        # Importar vistas aquí para evitar importaciones circulares
        self._views: Dict[str, ctk.CTkFrame] = {}
        self._active_button = None

        # Mostrar dashboard al inicio
        self._navigate_to("dashboard")

        # Cleanup al cerrar
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Sidebar ───────────────────────────────────────────────────────────

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self, width=SIDEBAR_WIDTH, corner_radius=0, fg_color=SIDEBAR_COLOR
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)  # empuja el resto hacia arriba
        self.sidebar.grid_propagate(False)

        # Logo / Título
        title_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=15, pady=(20, 5), sticky="ew")

        ctk.CTkLabel(
            title_frame, text="💰", font=ctk.CTkFont(size=32)
        ).pack()
        ctk.CTkLabel(
            title_frame,
            text="Finanzas\nPersonales",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack()

        # Separador
        ctk.CTkFrame(self.sidebar, height=1, fg_color=ACCENT_COLOR).grid(
            row=1, column=0, padx=15, pady=10, sticky="ew"
        )

        # Botones de navegación
        nav_items = [
            ("dashboard",    "🏠  Dashboard"),
            ("transactions", "💳  Transacciones"),
            ("categories",   "🏷️  Categorías"),
            ("stats",        "📊  Estadísticas"),
            ("investments",  "📈  Inversiones"),
        ]
        self._nav_buttons = {}
        for i, (key, label) in enumerate(nav_items):
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                anchor="w",
                font=ctk.CTkFont(size=13),
                fg_color="transparent",
                hover_color=ACCENT_COLOR,
                text_color=TEXT_SECONDARY,
                height=42,
                corner_radius=8,
                command=lambda k=key: self._navigate_to(k),
            )
            btn.grid(row=i + 2, column=0, padx=10, pady=2, sticky="ew")
            self._nav_buttons[key] = btn

        # Versión al fondo
        ctk.CTkLabel(
            self.sidebar,
            text="v1.0.0  —  Local",
            font=ctk.CTkFont(size=10),
            text_color=TEXT_SECONDARY,
        ).grid(row=11, column=0, padx=10, pady=15, sticky="s")

    # ── Área de contenido ─────────────────────────────────────────────────

    def _build_content_area(self):
        self.content_frame = ctk.CTkFrame(
            self, corner_radius=0, fg_color=BG_COLOR
        )
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=0)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

    # ── Navegación ────────────────────────────────────────────────────────

    def _navigate_to(self, key: str):
        """Muestra la vista correspondiente, creándola si no existe."""
        # Resaltar botón activo
        if self._active_button:
            self._active_button.configure(
                fg_color="transparent", text_color=TEXT_SECONDARY
            )
        btn = self._nav_buttons.get(key)
        if btn:
            btn.configure(fg_color=ACCENT_COLOR, text_color="#ffffff")
            self._active_button = btn

        # Ocultar vista actual
        for view in self._views.values():
            view.grid_forget()

        # Crear o mostrar la vista
        if key not in self._views:
            self._views[key] = self._create_view(key)

        if self._views[key]:
            self._views[key].grid(row=0, column=0, sticky="nsew")

    def _create_view(self, key: str) -> ctk.CTkFrame:
        """Instancia la vista solicitada."""
        try:
            from app.views.dashboard_view import DashboardView
            from app.views.transaction_view import TransactionView
            from app.views.category_view import CategoryView
            from app.views.stats_view import StatsView
            from app.views.investment_view import InvestmentView

            views_map = {
                "dashboard": DashboardView,
                "transactions": TransactionView,
                "categories": CategoryView,
                "stats": StatsView,
                "investments": InvestmentView,
            }

            ViewClass = views_map.get(key)

            if ViewClass:
                return ViewClass(
                    self.content_frame,
                    session=self._session,
                    navigate=self._navigate_to
                )

        except Exception as e:
            return self._error_view(f"Error cargando vista:\n{str(e)}")

        return self._error_view(f"Vista '{key}' no implementada")
    
    def _error_view(self, message: str) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.content_frame, fg_color=BG_COLOR)

        label = ctk.CTkLabel(
            frame,
            text=message,
            text_color="#ff6b6b",
            font=ctk.CTkFont(size=14),
            wraplength=400,
            justify="center"
        )
        label.pack(expand=True)

        return frame

    def refresh_view(self, key: str):
        """Elimina y recrea una vista para forzar actualización de datos."""
        if key in self._views:
            self._views[key].destroy()
            del self._views[key]
        self._navigate_to(key)

    # ── Cierre ────────────────────────────────────────────────────────────

    def _on_close(self):
        if self._session:
            self._session.close()
        self.destroy()