"""
Ventana principal de la aplicación.
Mejoras implementadas:
  #10  Persiste la última vista activa (config.json)
  #11  Toggle light/dark mode en el sidebar
"""

import customtkinter as ctk
from typing import Dict

from app.database.connection import get_session
from app.utils import config as cfg

ctk.set_appearance_mode(cfg.get("theme") or "dark")
ctk.set_default_color_theme("blue")

SIDEBAR_WIDTH  = 200
BG_COLOR       = "#1a1a2e"
SIDEBAR_COLOR  = "#16213e"
ACCENT_COLOR   = "#0f3460"
HIGHLIGHT_COLOR = "#e94560"
TEXT_PRIMARY   = "#e0e0e0"
TEXT_SECONDARY = "#a0a0b0"


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("💰 Finanzas Personales")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(fg_color=BG_COLOR)

        self._session = get_session()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_content_area()

        self._views: Dict[str, ctk.CTkFrame] = {}
        self._active_button = None

        # MEJORA #10: arrancar en la última vista visitada
        last = cfg.get("last_view") or "dashboard"
        self._navigate_to(last)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Sidebar ───────────────────────────────────────────────────────────

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self, width=SIDEBAR_WIDTH, corner_radius=0, fg_color=SIDEBAR_COLOR
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)
        self.sidebar.grid_propagate(False)

        # Logo
        title_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=15, pady=(20, 5), sticky="ew")
        ctk.CTkLabel(title_frame, text="💰", font=ctk.CTkFont(size=32)).pack()
        ctk.CTkLabel(
            title_frame, text="Finanzas\nPersonales",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_PRIMARY,
        ).pack()

        ctk.CTkFrame(self.sidebar, height=1, fg_color=ACCENT_COLOR).grid(
            row=1, column=0, padx=15, pady=10, sticky="ew"
        )

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
                self.sidebar, text=label, anchor="w",
                font=ctk.CTkFont(size=13),
                fg_color="transparent", hover_color=ACCENT_COLOR,
                text_color=TEXT_SECONDARY, height=42, corner_radius=8,
                command=lambda k=key: self._navigate_to(k),
            )
            btn.grid(row=i + 2, column=0, padx=10, pady=2, sticky="ew")
            self._nav_buttons[key] = btn

        # Separador inferior
        ctk.CTkFrame(self.sidebar, height=1, fg_color=ACCENT_COLOR).grid(
            row=9, column=0, padx=15, pady=(10, 5), sticky="ew"
        )

        # MEJORA #11: Toggle de tema
        self._theme_btn = ctk.CTkButton(
            self.sidebar,
            text=self._theme_label(),
            anchor="w",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color=ACCENT_COLOR,
            text_color=TEXT_SECONDARY,
            height=36,
            corner_radius=8,
            command=self._toggle_theme,
        )
        self._theme_btn.grid(row=10, column=0, padx=10, pady=2, sticky="ew")

        ctk.CTkLabel(
            self.sidebar, text="v1.1.0  —  Local",
            font=ctk.CTkFont(size=10), text_color=TEXT_SECONDARY,
        ).grid(row=11, column=0, padx=10, pady=(2, 15), sticky="s")

    # ── Tema (MEJORA #11) ─────────────────────────────────────────────────

    def _theme_label(self) -> str:
        mode = ctk.get_appearance_mode()
        return "☀️  Modo claro" if mode == "Dark" else "🌙  Modo oscuro"

    def _toggle_theme(self):
        current = ctk.get_appearance_mode()
        new_mode = "light" if current == "Dark" else "dark"
        ctk.set_appearance_mode(new_mode)
        cfg.set("theme", new_mode)
        self._theme_btn.configure(text=self._theme_label())

    # ── Área de contenido ─────────────────────────────────────────────────

    def _build_content_area(self):
        self.content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=BG_COLOR)
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

    # ── Navegación (MEJORA #10: guarda última vista) ──────────────────────

    def _navigate_to(self, key: str):
        if self._active_button:
            self._active_button.configure(
                fg_color="transparent", text_color=TEXT_SECONDARY
            )
        btn = self._nav_buttons.get(key)
        if btn:
            btn.configure(fg_color=ACCENT_COLOR, text_color="#ffffff")
            self._active_button = btn

        for view in self._views.values():
            view.grid_forget()

        if key not in self._views:
            self._views[key] = self._create_view(key)

        if self._views.get(key):
            self._views[key].grid(row=0, column=0, sticky="nsew")

        # MEJORA #10: persistir la vista activa
        cfg.set("last_view", key)

    def _create_view(self, key: str) -> ctk.CTkFrame:
        from app.views.dashboard_view import DashboardView
        from app.views.transaction_view import TransactionView
        from app.views.category_view import CategoryView
        from app.views.stats_view import StatsView
        from app.views.investment_view import InvestmentView

        views_map = {
            "dashboard":    DashboardView,
            "transactions": TransactionView,
            "categories":   CategoryView,
            "stats":        StatsView,
            "investments":  InvestmentView,
        }
        ViewClass = views_map.get(key)
        if ViewClass:
            return ViewClass(self.content_frame, session=self._session, navigate=self._navigate_to)
        return None

    def refresh_view(self, key: str):
        if key in self._views:
            self._views[key].destroy()
            del self._views[key]
        self._navigate_to(key)

    def _on_close(self):
        if self._session:
            self._session.close()
        self.destroy()
