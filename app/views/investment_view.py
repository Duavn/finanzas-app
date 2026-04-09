"""
Vista de Inversiones y Ahorros.
Mejoras implementadas:
  #2  Loading overlay al cargar datos
  #7  Tooltips descriptivos en botones de acción
  #8  Toast de confirmación al guardar / actualizar / eliminar
"""

import customtkinter as ctk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import date
from typing import Callable, Optional

from sqlalchemy.orm import Session

from app.services.investment_service import InvestmentService
from app.utils.charts import chart_portafolio_inversiones
from app.utils.validators import validate_monto, validate_fecha, validate_nombre
from app.utils.ui_helpers import show_toast, set_error, Tooltip, LoadingOverlay

BG      = "#1a1a2e"
PANEL   = "#16213e"
ACCENT  = "#0f3460"
GREEN   = "#2ecc71"
RED     = "#e74c3c"
GOLD    = "#f39c12"
TEXT    = "#e0e0e0"
TEXT2   = "#a0a0b0"
INPUT_BG = "#0d1b2a"


class InvestmentView(ctk.CTkFrame):
    def __init__(self, parent, session: Session, navigate: Callable):
        super().__init__(parent, fg_color=BG, corner_radius=0)
        self.session = session
        self.navigate = navigate
        self.inv_service = InvestmentService(session)
        self._chart_canvas = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_body()

        # MEJORA #2
        self._overlay = LoadingOverlay(self)
        self._load_data()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=0, height=60)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header, text="📈  Inversiones & Ahorros",
            font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT
        ).grid(row=0, column=0, padx=20, pady=15, sticky="w")

        ctk.CTkButton(
            header, text="+ Nueva Inversión", width=150,
            fg_color=GOLD, hover_color="#d68910", text_color="#000000",
            command=self._open_form
        ).grid(row=0, column=2, padx=20, pady=15)

    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=1)

        self.kpi_frame = ctk.CTkFrame(body, fg_color=PANEL, corner_radius=12)
        self.kpi_frame.grid(row=0, column=0, padx=15, pady=15, sticky="ew")
        self.kpi_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        main = ctk.CTkFrame(body, fg_color=BG, corner_radius=0)
        main.grid(row=1, column=0, sticky="nsew")
        main.grid_columnconfigure(0, weight=2)
        main.grid_columnconfigure(1, weight=3)
        main.grid_rowconfigure(0, weight=1)

        self.chart_frame = ctk.CTkFrame(main, fg_color=PANEL, corner_radius=12)
        self.chart_frame.grid(row=0, column=0, padx=(15, 5), pady=(0, 15), sticky="nsew")
        ctk.CTkLabel(
            self.chart_frame, text="Portafolio",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT
        ).pack(padx=15, pady=(12, 0), anchor="w")

        table_f = ctk.CTkFrame(main, fg_color=PANEL, corner_radius=12)
        table_f.grid(row=0, column=1, padx=(5, 15), pady=(0, 15), sticky="nsew")
        table_f.grid_columnconfigure(0, weight=1)
        table_f.grid_rowconfigure(1, weight=1)

        th = ctk.CTkFrame(table_f, fg_color=ACCENT, corner_radius=0, height=36)
        th.grid(row=0, column=0, sticky="ew")
        th.grid_propagate(False)
        th.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        for col, h in enumerate(["Nombre", "Tipo", "Inicial", "Actual", "Rend.", "Acciones"]):
            ctk.CTkLabel(th, text=h, font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=TEXT).grid(row=0, column=col, padx=8, pady=8, sticky="w")

        self.table_scroll = ctk.CTkScrollableFrame(table_f, fg_color="transparent")
        self.table_scroll.grid(row=1, column=0, sticky="nsew")
        self.table_scroll.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

    def _load_data(self):
        self._overlay.show("Cargando portafolio...")
        self.after(60, self._do_load_data)

    def _do_load_data(self):
        try:
            for w in self.kpi_frame.winfo_children():
                w.destroy()
            resumen = self.inv_service.get_resumen()
            kpis = [
                ("📦 Inversiones", str(resumen["cantidad"]), TEXT),
                ("💰 Total Invertido", f"${resumen['total_inicial']:,.2f}", TEXT2),
                ("📈 Valor Actual", f"${resumen['total_actual']:,.2f}", GOLD),
                ("🎯 Rendimiento",
                 f"{resumen['rendimiento_porcentaje']:+.2f}%",
                 GREEN if resumen["rendimiento_porcentaje"] >= 0 else RED),
            ]
            for i, (title, value, color) in enumerate(kpis):
                f = ctk.CTkFrame(self.kpi_frame, fg_color=BG, corner_radius=8)
                f.grid(row=0, column=i, padx=8, pady=12, sticky="ew")
                ctk.CTkLabel(f, text=title, font=ctk.CTkFont(size=10), text_color=TEXT2).pack(pady=(10, 2))
                ctk.CTkLabel(f, text=value, font=ctk.CTkFont(size=15, weight="bold"),
                             text_color=color).pack(pady=(0, 10))

            inversiones = self.inv_service.get_all()

            # Gráfico
            if self._chart_canvas:
                try:
                    self._chart_canvas.get_tk_widget().destroy()
                except Exception:
                    pass
            for w in self.chart_frame.winfo_children():
                if not isinstance(w, ctk.CTkLabel):
                    w.destroy()
            fig = chart_portafolio_inversiones([inv.to_dict() for inv in inversiones], width=4, height=4)
            self._chart_canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            self._chart_canvas.draw()
            self._chart_canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

            # Tabla
            for w in self.table_scroll.winfo_children():
                w.destroy()

            if not inversiones:
                ctk.CTkLabel(
                    self.table_scroll, text="Sin inversiones registradas.",
                    text_color=TEXT2, font=ctk.CTkFont(size=12)
                ).grid(row=0, column=0, columnspan=6, pady=30)
                return

            for i, inv in enumerate(inversiones):
                d = inv.to_dict()
                rend_color = GREEN if d["rendimiento"] >= 0 else RED
                row_vals = [
                    (d["nombre"][:20], TEXT),
                    (d["tipo"].capitalize(), TEXT2),
                    (f"${d['monto_inicial']:,.2f}", TEXT2),
                    (f"${d['monto_actual']:,.2f}", GOLD),
                    (f"{d['rendimiento']:+.1f}%", rend_color),
                ]
                for col, (val, clr) in enumerate(row_vals):
                    ctk.CTkLabel(
                        self.table_scroll, text=val,
                        font=ctk.CTkFont(size=11), text_color=clr, anchor="w"
                    ).grid(row=i, column=col, padx=8, pady=6, sticky="w")

                # MEJORA #7: Tooltips en los tres botones de acción
                actions = ctk.CTkFrame(self.table_scroll, fg_color="transparent")
                actions.grid(row=i, column=5, padx=4, pady=4, sticky="w")

                update_btn = ctk.CTkButton(
                    actions, text="💰", width=30, height=28,
                    fg_color=ACCENT, hover_color="#1a4a7a",
                    command=lambda iid=inv.id: self._update_valor(iid)
                )
                update_btn.pack(side="left", padx=2)
                Tooltip(update_btn, "Actualizar valor actual")

                edit_btn = ctk.CTkButton(
                    actions, text="✏️", width=30, height=28,
                    fg_color=ACCENT, hover_color="#1a4a7a",
                    command=lambda iid=inv.id: self._open_form(iid)
                )
                edit_btn.pack(side="left", padx=2)
                Tooltip(edit_btn, "Editar inversión")

                del_btn = ctk.CTkButton(
                    actions, text="🗑️", width=30, height=28,
                    fg_color="#4a1020", hover_color=RED,
                    command=lambda iid=inv.id: self._delete(iid)
                )
                del_btn.pack(side="left", padx=2)
                Tooltip(del_btn, "Eliminar inversión")

        finally:
            self._overlay.hide()

    def _open_form(self, inv_id: Optional[int] = None):
        inv = self.inv_service.get_by_id(inv_id) if inv_id else None
        win = ctk.CTkToplevel(self)
        win.title("Nueva Inversión" if not inv else "Editar Inversión")
        win.geometry("420x510")
        win.grab_set()
        win.configure(fg_color=BG)
        win.resizable(False, False)
        win.bind("<Escape>", lambda e: win.destroy())

        ctk.CTkLabel(
            win,
            text="📈 Nueva Inversión" if not inv else "✏️ Editar Inversión",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT
        ).pack(pady=(20, 10))

        form = ctk.CTkFrame(win, fg_color=PANEL, corner_radius=12)
        form.pack(fill="both", expand=True, padx=20, pady=10)
        form.grid_columnconfigure(0, weight=1)

        def lbl(text, row):
            ctk.CTkLabel(form, text=text, text_color=TEXT2,
                         font=ctk.CTkFont(size=11)
                         ).grid(row=row, column=0, padx=20, pady=(10, 2), sticky="w")

        lbl("Nombre *", 0)
        nombre_e = ctk.CTkEntry(form, placeholder_text="Ej: Fondo de emergencia", fg_color=INPUT_BG)
        nombre_e.grid(row=1, column=0, padx=20, pady=(0, 5), sticky="ew")
        if inv: nombre_e.insert(0, inv.nombre)

        lbl("Tipo *", 2)
        tipo_var = ctk.StringVar(value=inv.tipo if inv else "ahorro")
        ctk.CTkOptionMenu(
            form, values=InvestmentService.TIPOS_VALIDOS, variable=tipo_var,
            fg_color=INPUT_BG, button_color=ACCENT
        ).grid(row=3, column=0, padx=20, pady=(0, 5), sticky="ew")

        lbl("Monto Inicial *", 4)
        inicial_e = ctk.CTkEntry(form, placeholder_text="Ej: 1000000", fg_color=INPUT_BG)
        inicial_e.grid(row=5, column=0, padx=20, pady=(0, 5), sticky="ew")
        if inv: inicial_e.insert(0, str(inv.monto_inicial))

        lbl("Monto Actual (vacío = igual al inicial)", 6)
        actual_e = ctk.CTkEntry(form, placeholder_text="Dejar vacío = igual al inicial", fg_color=INPUT_BG)
        actual_e.grid(row=7, column=0, padx=20, pady=(0, 5), sticky="ew")
        if inv: actual_e.insert(0, str(inv.monto_actual))

        lbl("Fecha de Inicio *", 8)
        fecha_e = ctk.CTkEntry(form, placeholder_text="DD/MM/YYYY", fg_color=INPUT_BG)
        fecha_e.grid(row=9, column=0, padx=20, pady=(0, 5), sticky="ew")
        fecha_e.insert(0, inv.fecha_inicio.strftime("%d/%m/%Y") if inv else date.today().strftime("%d/%m/%Y"))

        lbl("Notas (opcional)", 10)
        notas_e = ctk.CTkEntry(form, placeholder_text="Observaciones", fg_color=INPUT_BG)
        notas_e.grid(row=11, column=0, padx=20, pady=(0, 5), sticky="ew")
        if inv and inv.notas: notas_e.insert(0, inv.notas)

        # MEJORA #3
        err_lbl = ctk.CTkLabel(form, text="", text_color=RED, font=ctk.CTkFont(size=11))
        err_lbl.grid(row=12, column=0, padx=20, pady=(5, 0))

        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(pady=12)

        def save():
            ok_n, nombre, msg_n = validate_nombre(nombre_e.get())
            if not ok_n: set_error(err_lbl, msg_n); return
            ok_m, monto_i, msg_m = validate_monto(inicial_e.get())
            if not ok_m: set_error(err_lbl, msg_m); return
            ok_f, fecha, msg_f = validate_fecha(fecha_e.get())
            if not ok_f: set_error(err_lbl, msg_f); return

            actual_str = actual_e.get().strip()
            monto_a = None
            if actual_str:
                ok_a, monto_a, msg_a = validate_monto(actual_str)
                if not ok_a: set_error(err_lbl, msg_a); return

            try:
                if inv:
                    self.inv_service.update(
                        inv.id, nombre=nombre, tipo=tipo_var.get(),
                        monto_inicial=monto_i, monto_actual=monto_a or monto_i,
                        fecha_inicio=fecha, notas=notas_e.get()
                    )
                    toast_msg = f"'{nombre}' actualizado."
                else:
                    self.inv_service.create(
                        nombre=nombre, tipo=tipo_var.get(),
                        monto_inicial=monto_i, fecha_inicio=fecha,
                        monto_actual=monto_a, notas=notas_e.get()
                    )
                    toast_msg = f"Inversión '{nombre}' creada."
                win.destroy()
                self._load_data()
                show_toast(self, toast_msg, kind="success")  # MEJORA #8
            except ValueError as e:
                set_error(err_lbl, str(e))

        ctk.CTkButton(
            btn_frame, text="💾 Guardar",
            fg_color=GOLD, hover_color="#d68910", text_color="#000000",
            width=130, command=save
        ).pack(side="left", padx=8)
        ctk.CTkButton(
            btn_frame, text="Cancelar",
            fg_color="transparent", hover_color=ACCENT, border_width=1,
            width=100, command=win.destroy
        ).pack(side="left", padx=8)

        win.bind("<Return>", lambda e: save())
        nombre_e.focus_set()

    def _update_valor(self, inv_id: int):
        inv = self.inv_service.get_by_id(inv_id)
        if not inv: return
        win = ctk.CTkToplevel(self)
        win.title("Actualizar Valor")
        win.geometry("340x250")
        win.grab_set()
        win.configure(fg_color=BG)
        win.resizable(False, False)
        win.bind("<Escape>", lambda e: win.destroy())

        ctk.CTkLabel(
            win, text=f"💰 Actualizar: {inv.nombre}",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT
        ).pack(pady=(20, 5))
        ctk.CTkLabel(
            win, text=f"Valor actual: ${inv.monto_actual:,.2f}",
            text_color=TEXT2, font=ctk.CTkFont(size=12)
        ).pack()

        form = ctk.CTkFrame(win, fg_color=PANEL, corner_radius=12)
        form.pack(fill="x", padx=20, pady=15)
        form.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(form, text="Nuevo valor actual:", text_color=TEXT2,
                     font=ctk.CTkFont(size=11)).grid(row=0, column=0, padx=20, pady=(15, 2), sticky="w")
        monto_e = ctk.CTkEntry(form, placeholder_text="Nuevo monto", fg_color=INPUT_BG)
        monto_e.grid(row=1, column=0, padx=20, pady=(0, 5), sticky="ew")
        monto_e.insert(0, str(inv.monto_actual))

        err_lbl = ctk.CTkLabel(form, text="", text_color=RED, font=ctk.CTkFont(size=11))
        err_lbl.grid(row=2, column=0, padx=20, pady=(5, 10))

        btn_f = ctk.CTkFrame(win, fg_color="transparent")
        btn_f.pack()

        def save():
            ok, monto, msg = validate_monto(monto_e.get())
            if not ok: set_error(err_lbl, msg); return
            try:
                self.inv_service.update_valor(inv_id, monto)
                win.destroy()
                self._load_data()
                show_toast(self, f"Valor de '{inv.nombre}' actualizado a ${monto:,.0f}.", kind="success")
            except ValueError as e:
                set_error(err_lbl, str(e))

        ctk.CTkButton(btn_f, text="💾 Guardar", fg_color=GOLD, hover_color="#d68910",
                       text_color="#000000", width=120, command=save).pack(side="left", padx=8)
        ctk.CTkButton(btn_f, text="Cancelar", fg_color="transparent",
                       hover_color=ACCENT, border_width=1, width=90,
                       command=win.destroy).pack(side="left", padx=8)

        win.bind("<Return>", lambda e: save())
        monto_e.focus_set()

    def _delete(self, inv_id: int):
        inv = self.inv_service.get_by_id(inv_id)
        if not inv: return
        if messagebox.askyesno("Confirmar", f"¿Eliminar '{inv.nombre}'?"):
            try:
                nombre = inv.nombre
                self.inv_service.delete(inv_id)
                self._load_data()
                show_toast(self, f"'{nombre}' eliminado.", kind="info")  # MEJORA #8
            except ValueError as e:
                messagebox.showerror("Error", str(e))
