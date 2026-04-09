"""
Vista de Estadísticas avanzadas.
Gráficos con filtros de fecha y análisis por categoría.
"""

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from datetime import date
from typing import Callable

from sqlalchemy.orm import Session

from app.services.transaction_service import TransactionService
from app.services.category_service import CategoryService
from app.utils.charts import chart_gastos_por_categoria, chart_evolucion_mensual
from app.utils.validators import validate_fecha


BG = "#1a1a2e"
PANEL = "#16213e"
ACCENT = "#0f3460"
GREEN = "#2ecc71"
RED = "#e74c3c"
TEXT = "#e0e0e0"
TEXT2 = "#a0a0b0"
INPUT_BG = "#0d1b2a"


class StatsView(ctk.CTkFrame):
    def __init__(self, parent, session: Session, navigate: Callable):
        super().__init__(parent, fg_color=BG, corner_radius=0)

        self.session = session
        self.navigate = navigate

        self.tx_service = TransactionService(session)
        self.cat_service = CategoryService(session)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_body()
        self._load_data()

    # ── HEADER ─────────────────────────────────────────────

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=0, height=60)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(5, weight=1)

        ctk.CTkLabel(
            header,
            text="📊  Estadísticas",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=TEXT
        ).grid(row=0, column=0, padx=20, pady=15, sticky="w")

        # Filtros fecha
        ctk.CTkLabel(header, text="Desde:", text_color=TEXT2).grid(row=0, column=1, padx=(20, 4))
        self.desde_entry = ctk.CTkEntry(header, placeholder_text="DD/MM/YYYY", width=115, fg_color=INPUT_BG)
        self.desde_entry.grid(row=0, column=2, padx=(0, 12))

        ctk.CTkLabel(header, text="Hasta:", text_color=TEXT2).grid(row=0, column=3, padx=(0, 4))
        self.hasta_entry = ctk.CTkEntry(header, placeholder_text="DD/MM/YYYY", width=115, fg_color=INPUT_BG)
        self.hasta_entry.grid(row=0, column=4, padx=(0, 12))

        # Valores por defecto
        today = date.today()
        self.desde_entry.insert(0, date(today.year, 1, 1).strftime("%d/%m/%Y"))
        self.hasta_entry.insert(0, today.strftime("%d/%m/%Y"))

        ctk.CTkButton(
            header,
            text="📊 Generar",
            fg_color=ACCENT,
            command=self._load_data
        ).grid(row=0, column=6, padx=20)

    # ── BODY ─────────────────────────────────────────────

    def _build_body(self):
        self.body = ctk.CTkScrollableFrame(self, fg_color=BG)
        self.body.grid(row=1, column=0, sticky="nsew")
        self.body.grid_columnconfigure((0, 1), weight=1)

    # ── UTIL ─────────────────────────────────────────────

    def _get_date_range(self):
        ok1, fd, _ = validate_fecha(self.desde_entry.get())
        ok2, fh, _ = validate_fecha(self.hasta_entry.get())
        return fd if ok1 else None, fh if ok2 else None

    # ── LOAD DATA ─────────────────────────────────────────────

    def _load_data(self):
        for w in self.body.winfo_children():
            w.destroy()

        try:
            fecha_desde, fecha_hasta = self._get_date_range()

            totales = self.tx_service.get_totales(fecha_desde, fecha_hasta)

            ahorro_pct = (
                (totales["balance"] / totales["ingreso"] * 100)
                if totales["ingreso"] > 0 else None
            )

            # ── KPI ──
            kpi_frame = ctk.CTkFrame(self.body, fg_color=PANEL, corner_radius=12)
            kpi_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
            kpi_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

            kpis = [
                ("Ingresos", f"${totales['ingreso']:,.2f}", GREEN),
                ("Gastos", f"${totales['gasto']:,.2f}", RED),
                ("Balance", f"${totales['balance']:,.2f}", GREEN if totales["balance"] >= 0 else RED),
                ("Ahorro", f"{ahorro_pct:.1f}%" if ahorro_pct else "N/A", GREEN),
                ("Transacciones", str(len(self.tx_service.get_all(
                    fecha_desde=fecha_desde, fecha_hasta=fecha_hasta))), "#3498db"),
            ]

            for i, (title, value, color) in enumerate(kpis):
                card = ctk.CTkFrame(kpi_frame, fg_color=BG)
                card.grid(row=0, column=i, padx=8, pady=12, sticky="ew")

                ctk.CTkLabel(card, text=title, text_color=TEXT2).pack()
                ctk.CTkLabel(card, text=value, text_color=color,
                             font=ctk.CTkFont(size=15, weight="bold")).pack()

            # ── GRÁFICO 1 ──
            frame1 = ctk.CTkFrame(self.body, fg_color=PANEL)
            frame1.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

            data1 = self.tx_service.get_gastos_por_categoria(fecha_desde, fecha_hasta)
            fig1 = chart_gastos_por_categoria(data1)

            canvas1 = FigureCanvasTkAgg(fig1, master=frame1)
            canvas1.draw()
            canvas1.get_tk_widget().pack(fill="both", expand=True)

            plt.close(fig1)

            # ── GRÁFICO 2 ──
            frame2 = ctk.CTkFrame(self.body, fg_color=PANEL)
            frame2.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

            data2 = self.tx_service.get_evolucion_mensual(fecha_desde, fecha_hasta)
            fig2 = chart_evolucion_mensual(data2)

            canvas2 = FigureCanvasTkAgg(fig2, master=frame2)
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill="both", expand=True)

            plt.close(fig2)

        except Exception as e:
            ctk.CTkLabel(
                self.body,
                text=f"Error cargando estadísticas:\n{str(e)}",
                text_color="red"
            ).pack(pady=50)