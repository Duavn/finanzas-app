"""
Vista de Inversiones y Ahorros.
Registra y muestra el portafolio con gráfico de comparativa.
"""

import customtkinter as ctk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from datetime import date
from typing import Callable, Optional

from sqlalchemy.orm import Session

from app.services.investment_service import InvestmentService
from app.utils.charts import chart_portafolio_inversiones
from app.utils.validators import validate_monto, validate_fecha, validate_nombre

BG = "#1a1a2e"
PANEL = "#16213e"
ACCENT = "#0f3460"
GREEN = "#2ecc71"
RED = "#e74c3c"
GOLD = "#f39c12"
TEXT = "#e0e0e0"
TEXT2 = "#a0a0b0"
INPUT_BG = "#0d1b2a"


class InvestmentView(ctk.CTkFrame):
    def __init__(self, parent, session: Session, navigate: Callable):
        super().__init__(parent, fg_color=BG, corner_radius=0)

        self.session = session
        self.navigate = navigate
        self.inv_service = InvestmentService(session)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_body()
        self._load_data()

    # ── HEADER ─────────────────────────────

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=PANEL, height=60)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)

        ctk.CTkLabel(
            header,
            text="📈 Inversiones & Ahorros",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=TEXT
        ).grid(row=0, column=0, padx=20, pady=15, sticky="w")

        ctk.CTkButton(
            header,
            text="+ Nueva Inversión",
            fg_color=GOLD,
            hover_color="#d68910",
            text_color="#000000",
            command=self._open_form
        ).grid(row=0, column=1, padx=20)

    # ── BODY ─────────────────────────────

    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color=BG)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=1)

        self.kpi_frame = ctk.CTkFrame(body, fg_color=PANEL)
        self.kpi_frame.grid(row=0, column=0, padx=15, pady=15, sticky="ew")

        self.chart_frame = ctk.CTkFrame(body, fg_color=PANEL)
        self.chart_frame.grid(row=1, column=0, padx=15, pady=10, sticky="nsew")

        self.table_frame = ctk.CTkScrollableFrame(body)
        self.table_frame.grid(row=2, column=0, padx=15, pady=10, sticky="nsew")

    # ── LOAD DATA ─────────────────────────────

    def _load_data(self):
        try:
            # limpiar
            for w in self.kpi_frame.winfo_children():
                w.destroy()
            for w in self.chart_frame.winfo_children():
                w.destroy()
            for w in self.table_frame.winfo_children():
                w.destroy()

            resumen = self.inv_service.get_resumen()

            # KPIs
            kpis = [
                ("Inversiones", resumen["cantidad"], TEXT),
                ("Invertido", f"${resumen['total_inicial']:,.2f}", TEXT2),
                ("Actual", f"${resumen['total_actual']:,.2f}", GOLD),
                ("Rendimiento", f"{resumen['rendimiento_porcentaje']:.2f}%",
                 GREEN if resumen["rendimiento_porcentaje"] >= 0 else RED),
            ]

            for i, (title, val, color) in enumerate(kpis):
                f = ctk.CTkFrame(self.kpi_frame, fg_color=BG)
                f.grid(row=0, column=i, padx=8, pady=10)
                ctk.CTkLabel(f, text=title, text_color=TEXT2).pack()
                ctk.CTkLabel(f, text=str(val), text_color=color).pack()

            inversiones = self.inv_service.get_all()

            # ── GRÁFICO ──
            fig = chart_portafolio_inversiones([i.to_dict() for i in inversiones])
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

            plt.close(fig)  # 🔥 evita fuga de memoria

            # ── TABLA ──
            for i, inv in enumerate(inversiones):
                d = inv.to_dict()

                values = [
                    d["nombre"],
                    d["tipo"],
                    f"${d['monto_inicial']:,.2f}",
                    f"${d['monto_actual']:,.2f}",
                    f"{d['rendimiento']:.2f}%"
                ]

                for col, val in enumerate(values):
                    ctk.CTkLabel(self.table_frame, text=val).grid(
                        row=i, column=col, padx=5, pady=5, sticky="w"
                    )

                btn = ctk.CTkButton(
                    self.table_frame,
                    text="Eliminar",
                    fg_color=RED,
                    command=lambda iid=inv.id: self._delete(iid)
                )
                btn.grid(row=i, column=5)

        except Exception as e:
            ctk.CTkLabel(
                self,
                text=f"Error:\n{str(e)}",
                text_color="red"
            ).pack(pady=50)

    # ── FORM ─────────────────────────────

    def _open_form(self, inv_id: Optional[int] = None):
        inv = self.inv_service.get_by_id(inv_id) if inv_id else None

        win = ctk.CTkToplevel(self)
        win.geometry("400x450")

        nombre = ctk.CTkEntry(win)
        nombre.pack()

        monto = ctk.CTkEntry(win)
        monto.pack()

        fecha = ctk.CTkEntry(win)
        fecha.pack()

        def save():
            ok_n, n, _ = validate_nombre(nombre.get())
            ok_m, m, _ = validate_monto(monto.get())
            ok_f, f, _ = validate_fecha(fecha.get())

            if not (ok_n and ok_m and ok_f):
                return

            self.inv_service.create(
                nombre=n,
                tipo="ahorro",
                monto_inicial=m,
                fecha_inicio=f
            )

            win.destroy()
            self._load_data()

        ctk.CTkButton(win, text="Guardar", command=save).pack()

    # ── DELETE ─────────────────────────────

    def _delete(self, inv_id: int):
        if messagebox.askyesno("Confirmar", "¿Eliminar inversión?"):
            self.inv_service.delete(inv_id)
            self._load_data()