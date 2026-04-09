"""
Vista del Dashboard.
"""

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from datetime import date, timedelta
from typing import Callable

from sqlalchemy.orm import Session

from app.services.transaction_service import TransactionService
from app.services.investment_service import InvestmentService
from app.utils.charts import chart_gastos_por_categoria, chart_evolucion_mensual

BG = "#1a1a2e"
PANEL = "#16213e"
ACCENT = "#0f3460"
GREEN = "#2ecc71"
RED = "#e74c3c"
BLUE = "#3498db"
GOLD = "#f39c12"
TEXT = "#e0e0e0"
TEXT2 = "#a0a0b0"


class DashboardView(ctk.CTkFrame):

    def __init__(self, parent, session: Session, navigate: Callable):
        super().__init__(parent, fg_color=BG)

        self.session = session
        self.navigate = navigate

        self.tx_service = TransactionService(session)
        self.inv_service = InvestmentService(session)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_body()
        self._load_data()

    # ───────── HEADER ─────────

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=PANEL, height=60)
        header.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            header,
            text="🏠 Dashboard",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=TEXT
        ).pack(side="left", padx=20)

        self.period_var = ctk.StringVar(value="Este mes")

        ctk.CTkOptionMenu(
            header,
            values=["Este mes", "Últimos 3 meses", "Últimos 6 meses", "Este año", "Todo"],
            variable=self.period_var,
            command=lambda _: self._load_data()
        ).pack(side="right", padx=20)

    # ───────── BODY ─────────

    def _build_body(self):
        self.body = ctk.CTkFrame(self, fg_color=BG)
        self.body.grid(row=1, column=0, sticky="nsew")

        # tarjetas
        self.card_ingreso = ctk.CTkLabel(self.body, text="$0", text_color=GREEN)
        self.card_ingreso.pack()

        self.card_gasto = ctk.CTkLabel(self.body, text="$0", text_color=RED)
        self.card_gasto.pack()

        self.card_balance = ctk.CTkLabel(self.body, text="$0", text_color=BLUE)
        self.card_balance.pack()

        self.card_inversion = ctk.CTkLabel(self.body, text="$0", text_color=GOLD)
        self.card_inversion.pack()

        self.chart1_canvas_frame = ctk.CTkFrame(self.body)
        self.chart1_canvas_frame.pack(fill="both", expand=True)

        self.chart2_canvas_frame = ctk.CTkFrame(self.body)
        self.chart2_canvas_frame.pack(fill="both", expand=True)

        self.recent_frame_inner = ctk.CTkFrame(self.body)
        self.recent_frame_inner.pack(fill="x")

    # ───────── LOGIC ─────────

    def _get_date_range(self):
        today = date.today()
        period = self.period_var.get()

        if period == "Este mes":
            return date(today.year, today.month, 1), today

        elif period == "Últimos 3 meses":
            return today - timedelta(days=90), today

        elif period == "Últimos 6 meses":
            return today - timedelta(days=180), today

        elif period == "Este año":
            return date(today.year, 1, 1), today

        elif period == "Todo":
            return None, None

        return None, None

    def _load_data(self):
        try:
            fecha_desde, fecha_hasta = self._get_date_range()

            totales = self.tx_service.get_totales(fecha_desde, fecha_hasta)

            balance = totales["balance"]

            self.card_ingreso.configure(text=f"${totales['ingreso']:,.2f}")
            self.card_gasto.configure(text=f"${totales['gasto']:,.2f}")
            self.card_balance.configure(text=f"${balance:,.2f}")

            resumen = self.inv_service.get_resumen()
            self.card_inversion.configure(text=f"${resumen['total_actual']:,.2f}")

            self._render_chart(
                self.chart1_canvas_frame,
                chart_gastos_por_categoria(
                    self.tx_service.get_gastos_por_categoria(fecha_desde, fecha_hasta)
                )
            )

            self._render_chart(
                self.chart2_canvas_frame,
                chart_evolucion_mensual(
                    self.tx_service.get_evolucion_mensual(fecha_desde, fecha_hasta)
                )
            )

            self._render_recent_transactions(fecha_desde, fecha_hasta)

        except Exception as e:
            for w in self.body.winfo_children():
                w.destroy()

            ctk.CTkLabel(
                self.body,
                text=f"Error:\n{str(e)}",
                text_color="red"
            ).pack(pady=50)

    # ───────── HELPERS ─────────

    def _render_chart(self, container, fig):
        for w in container.winfo_children():
            w.destroy()

        canvas = FigureCanvasTkAgg(fig, master=container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        plt.close(fig)

    def _render_recent_transactions(self, fecha_desde, fecha_hasta):
        for w in self.recent_frame_inner.winfo_children():
            w.destroy()

        txs = self.tx_service.get_all(fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)[:5]

        for tx in txs:
            d = tx.to_dict()
            ctk.CTkLabel(
                self.recent_frame_inner,
                text=f"{d['fecha']} - {d['tipo']} - ${float(d['monto']):,.2f}"
            ).pack(anchor="w")