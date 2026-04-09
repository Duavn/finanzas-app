"""
Vista del Dashboard.
Mejoras implementadas:
  #1  Gráficos responsivos (se recalculan al resize)
  #2  Loading overlay con spinner mientras cargan los datos
  #8  Toast de confirmación en acciones
  #9  Tendencia (↑↓%) en tarjetas KPI comparando con período anterior
"""

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import date, timedelta
from typing import Callable, Optional

from sqlalchemy.orm import Session

from app.services.transaction_service import TransactionService
from app.services.investment_service import InvestmentService
from app.utils.charts import chart_gastos_por_categoria, chart_evolucion_mensual
from app.utils.ui_helpers import LoadingOverlay, show_toast

BG    = "#1a1a2e"
PANEL = "#16213e"
ACCENT = "#0f3460"
GREEN  = "#2ecc71"
RED    = "#e74c3c"
BLUE   = "#3498db"
GOLD   = "#f39c12"
TEXT   = "#e0e0e0"
TEXT2  = "#a0a0b0"


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, session: Session, navigate: Callable):
        super().__init__(parent, fg_color=BG, corner_radius=0)
        self.session    = session
        self.navigate   = navigate
        self.tx_service  = TransactionService(session)
        self.inv_service = InvestmentService(session)

        # Canvas activos para poder destruirlos en resize
        self._chart_canvases = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_body()

        # MEJORA #2: overlay de carga
        self._overlay = LoadingOverlay(self)

        self._load_data()

    # ── Header ────────────────────────────────────────────────────────────

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=0, height=60)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        header.grid_propagate(False)

        ctk.CTkLabel(
            header, text="🏠  Dashboard",
            font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT
        ).grid(row=0, column=0, padx=20, pady=15, sticky="w")

        self.period_var = ctk.StringVar(value="Este mes")
        ctk.CTkOptionMenu(
            header,
            values=["Este mes", "Últimos 3 meses", "Últimos 6 meses", "Este año", "Todo"],
            variable=self.period_var,
            fg_color=ACCENT, button_color=ACCENT,
            command=lambda _: self._load_data(),
            width=160,
        ).grid(row=0, column=2, padx=20, pady=15, sticky="e")

        ctk.CTkButton(
            header, text="↺ Actualizar", width=110,
            fg_color=ACCENT, hover_color="#1a4a7a",
            command=self._load_data
        ).grid(row=0, column=3, padx=(0, 20), pady=15)

    # ── Body ──────────────────────────────────────────────────────────────

    def _build_body(self):
        body = ctk.CTkScrollableFrame(self, fg_color=BG, corner_radius=0)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.body = body

        # ── Tarjetas KPI ──
        self.card_ingreso   = self._make_card(body, "Ingresos",   "$0.00", GREEN, "💚", 0, 0)
        self.card_gasto     = self._make_card(body, "Gastos",     "$0.00", RED,   "❤️",  0, 1)
        self.card_balance   = self._make_card(body, "Balance",    "$0.00", BLUE,  "💙", 0, 2)
        self.card_inversion = self._make_card(body, "Portafolio", "$0.00", GOLD,  "💛", 0, 3)

        # ── Gráfico 1: Dona ──
        chart1_frame = ctk.CTkFrame(body, fg_color=PANEL, corner_radius=12)
        chart1_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        chart1_frame.grid_columnconfigure(0, weight=1)
        chart1_frame.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(
            chart1_frame, text="Gastos por Categoría",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT
        ).grid(row=0, column=0, padx=15, pady=(12, 0), sticky="w")
        self.chart1_host = ctk.CTkFrame(chart1_frame, fg_color="transparent")
        self.chart1_host.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        # MEJORA #1: bind resize
        self.chart1_host.bind("<Configure>", lambda e: self._on_chart1_resize(e))

        # ── Gráfico 2: Barras mensuales ──
        chart2_frame = ctk.CTkFrame(body, fg_color=PANEL, corner_radius=12)
        chart2_frame.grid(row=1, column=2, columnspan=2, padx=10, pady=10, sticky="nsew")
        chart2_frame.grid_columnconfigure(0, weight=1)
        chart2_frame.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(
            chart2_frame, text="Ingresos vs Gastos Mensuales",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT
        ).grid(row=0, column=0, padx=15, pady=(12, 0), sticky="w")
        self.chart2_host = ctk.CTkFrame(chart2_frame, fg_color="transparent")
        self.chart2_host.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.chart2_host.bind("<Configure>", lambda e: self._on_chart2_resize(e))

        # ── Últimas transacciones ──
        recent_frame = ctk.CTkFrame(body, fg_color=PANEL, corner_radius=12)
        recent_frame.grid(row=2, column=0, columnspan=4, padx=10, pady=10, sticky="ew")
        recent_frame.grid_columnconfigure(0, weight=1)
        hf = ctk.CTkFrame(recent_frame, fg_color="transparent")
        hf.grid(row=0, column=0, padx=15, pady=(12, 5), sticky="ew")
        hf.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            hf, text="Últimas Transacciones",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(
            hf, text="Ver todas →", width=100,
            fg_color="transparent", hover_color=ACCENT, text_color=BLUE,
            command=lambda: self.navigate("transactions")
        ).grid(row=0, column=2, sticky="e")
        self.recent_inner = ctk.CTkFrame(recent_frame, fg_color="transparent")
        self.recent_inner.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.recent_inner.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

    # ── Tarjeta con tendencia (MEJORA #9) ─────────────────────────────────

    def _make_card(self, parent, title, value, color, icon, row, col):
        card = ctk.CTkFrame(parent, fg_color=PANEL, corner_radius=12)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="ew")
        ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=24)).pack(pady=(15, 2))
        ctk.CTkLabel(
            card, text=title, font=ctk.CTkFont(size=11), text_color=TEXT2
        ).pack()
        value_lbl = ctk.CTkLabel(
            card, text=value,
            font=ctk.CTkFont(size=18, weight="bold"), text_color=color
        )
        value_lbl.pack(pady=(2, 2))
        # Label de tendencia — vacío hasta que carguen los datos
        trend_lbl = ctk.CTkLabel(
            card, text="", font=ctk.CTkFont(size=10), text_color=TEXT2
        )
        trend_lbl.pack(pady=(0, 12))
        # Retornar ambos labels empaquetados en un dict
        card._value_label = value_lbl
        card._trend_label = trend_lbl
        return card

    def _update_card(self, card, value_text: str, value_color: str,
                     pct: Optional[float], invert: bool = False):
        """
        Actualiza valor y tendencia de una tarjeta KPI.
        invert=True: para gastos, subir es malo (rojo).
        """
        card._value_label.configure(text=value_text, text_color=value_color)
        if pct is None:
            card._trend_label.configure(text="Sin datos previos", text_color=TEXT2)
            return
        arrow = "↑" if pct >= 0 else "↓"
        if invert:
            trend_color = RED if pct > 0 else GREEN
        else:
            trend_color = GREEN if pct >= 0 else RED
        card._trend_label.configure(
            text=f"{arrow} {abs(pct):.1f}% vs período anterior",
            text_color=trend_color,
        )

    # ── Resize responsivo (MEJORA #1) ─────────────────────────────────────

    def _on_chart1_resize(self, event):
        if hasattr(self, '_gastos_cat_data') and event.width > 10:
            self._render_chart(
                self.chart1_host,
                chart_gastos_por_categoria(
                    self._gastos_cat_data,
                    width=max(3, event.width / 100),
                    height=max(2.5, event.height / 100) if event.height > 50 else 3.5,
                ),
                key="chart1",
            )

    def _on_chart2_resize(self, event):
        if hasattr(self, '_evolucion_data') and event.width > 10:
            self._render_chart(
                self.chart2_host,
                chart_evolucion_mensual(
                    self._evolucion_data,
                    width=max(4, event.width / 100),
                    height=max(2.5, event.height / 100) if event.height > 50 else 3.5,
                ),
                key="chart2",
            )

    # ── Carga de datos con overlay (MEJORAS #2, #9) ───────────────────────

    def _get_date_range(self):
        today = date.today()
        p = self.period_var.get()
        if p == "Este mes":
            return date(today.year, today.month, 1), today
        elif p == "Últimos 3 meses":
            return today - timedelta(days=90), today
        elif p == "Últimos 6 meses":
            return today - timedelta(days=180), today
        elif p == "Este año":
            return date(today.year, 1, 1), today
        return None, None

    def _load_data(self):
        self._overlay.show("Cargando dashboard...")
        # Defer la carga real para que el overlay se pinte primero
        self.after(60, self._do_load_data)

    def _do_load_data(self):
        try:
            fecha_desde, fecha_hasta = self._get_date_range()

            # Tendencias
            tendencia = self.tx_service.get_tendencia(fecha_desde, fecha_hasta)

            balance = tendencia["balance_actual"]
            color_balance = GREEN if balance >= 0 else RED

            self._update_card(
                self.card_ingreso,
                f"${tendencia['ingreso_actual']:,.2f}", GREEN,
                tendencia["ingreso_pct"], invert=False,
            )
            self._update_card(
                self.card_gasto,
                f"${tendencia['gasto_actual']:,.2f}", RED,
                tendencia["gasto_pct"], invert=True,
            )
            self._update_card(
                self.card_balance,
                f"${balance:,.2f}", color_balance,
                tendencia["balance_pct"], invert=False,
            )

            resumen_inv = self.inv_service.get_resumen()
            self._update_card(
                self.card_inversion,
                f"${resumen_inv['total_actual']:,.2f}", GOLD,
                resumen_inv["rendimiento_porcentaje"] if resumen_inv["cantidad"] else None,
                invert=False,
            )

            # Gráficos — guardar datos para el resize responsivo
            self._gastos_cat_data = self.tx_service.get_gastos_por_categoria(fecha_desde, fecha_hasta)
            self._evolucion_data  = self.tx_service.get_evolucion_mensual(fecha_desde, fecha_hasta)

            self._render_chart(
                self.chart1_host,
                chart_gastos_por_categoria(self._gastos_cat_data, width=5, height=3.5),
                key="chart1",
            )
            self._render_chart(
                self.chart2_host,
                chart_evolucion_mensual(self._evolucion_data, width=6, height=3.5),
                key="chart2",
            )
            self._render_recent_transactions(fecha_desde, fecha_hasta)

        finally:
            self._overlay.hide()

    # ── Render de gráfico (MEJORA #1: destruye canvas anterior) ──────────

    def _render_chart(self, container, fig, key: str):
        # Destruir canvas previo para evitar memory leak
        if key in self._chart_canvases:
            try:
                self._chart_canvases[key].get_tk_widget().destroy()
            except Exception:
                pass
        for w in container.winfo_children():
            w.destroy()

        canvas = FigureCanvasTkAgg(fig, master=container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._chart_canvases[key] = canvas

    # ── Tabla de últimas transacciones ────────────────────────────────────

    def _render_recent_transactions(self, fecha_desde, fecha_hasta):
        for w in self.recent_inner.winfo_children():
            w.destroy()

        headers = ["Fecha", "Tipo", "Categoría", "Descripción", "Monto"]
        for col, h in enumerate(headers):
            ctk.CTkLabel(
                self.recent_inner, text=h,
                font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT2
            ).grid(row=0, column=col, padx=8, pady=(0, 5), sticky="w")

        txs = self.tx_service.get_all(
            fecha_desde=fecha_desde, fecha_hasta=fecha_hasta, limit=8
        )
        if not txs:
            ctk.CTkLabel(
                self.recent_inner, text="No hay transacciones en este período.",
                text_color=TEXT2, font=ctk.CTkFont(size=12)
            ).grid(row=1, column=0, columnspan=5, pady=15)
            return

        for row_i, tx in enumerate(txs, start=1):
            d = tx.to_dict()
            color_m = GREEN if d["tipo"] == "ingreso" else RED
            icon    = "⬆️" if d["tipo"] == "ingreso" else "⬇️"
            values  = [
                d["fecha"],
                f"{icon} {d['tipo'].capitalize()}",
                d["categoria_nombre"] or "—",
                (d["descripcion"] or "—")[:30],
                f"${d['monto']:,.2f}",
            ]
            colors = [TEXT, TEXT, TEXT, TEXT2, color_m]
            for col, (val, clr) in enumerate(zip(values, colors)):
                ctk.CTkLabel(
                    self.recent_inner, text=val,
                    font=ctk.CTkFont(size=11), text_color=clr, anchor="w"
                ).grid(row=row_i, column=col, padx=8, pady=3, sticky="w")
