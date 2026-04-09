"""
Vista de Transacciones.
Mejoras implementadas:
  #3  Auto-clear de mensajes de error (4 segundos)
  #4  Atajos de teclado: Enter para guardar, Escape para cerrar
  #5  Validación inline de fecha al perder el foco
  #6  Conteo de resultados + límite de paginación
  #8  Toast de éxito al guardar / eliminar
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import date
from typing import Callable, Optional

from sqlalchemy.orm import Session

from app.services.transaction_service import TransactionService
from app.services.category_service import CategoryService
from app.utils.validators import validate_monto, validate_fecha
from app.utils.ui_helpers import show_toast, set_error, LoadingOverlay

BG      = "#1a1a2e"
PANEL   = "#16213e"
ACCENT  = "#0f3460"
GREEN   = "#2ecc71"
RED     = "#e74c3c"
BLUE    = "#3498db"
TEXT    = "#e0e0e0"
TEXT2   = "#a0a0b0"
INPUT_BG = "#0d1b2a"

PAGE_SIZE = 100   # MEJORA #6: límite de filas en tabla


class TransactionView(ctk.CTkFrame):
    def __init__(self, parent, session: Session, navigate: Callable):
        super().__init__(parent, fg_color=BG, corner_radius=0)
        self.session    = session
        self.navigate   = navigate
        self.tx_service  = TransactionService(session)
        self.cat_service = CategoryService(session)
        self._editing_id: Optional[int] = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_body()
        self._load_transactions()

    # ── Header ────────────────────────────────────────────────────────────

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=0, height=60)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header, text="💳  Transacciones",
            font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT
        ).grid(row=0, column=0, padx=20, pady=15, sticky="w")

        ctk.CTkButton(
            header, text="+ Nueva Transacción", width=165,
            fg_color=GREEN, hover_color="#27ae60", text_color="#000000",
            command=self._open_form
        ).grid(row=0, column=2, padx=20, pady=15)

    # ── Body ──────────────────────────────────────────────────────────────

    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=1)

        # ── Filtros ──
        ff = ctk.CTkFrame(body, fg_color=PANEL, corner_radius=12)
        ff.grid(row=0, column=0, padx=15, pady=15, sticky="ew")
        ff.grid_columnconfigure((1, 3, 5), weight=1)

        ctk.CTkLabel(ff, text="Filtros:", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT).grid(row=0, column=0, padx=(15, 8), pady=12)

        ctk.CTkLabel(ff, text="Tipo:", text_color=TEXT2, font=ctk.CTkFont(size=11)
                     ).grid(row=0, column=1, padx=(0, 4), sticky="e")
        self.filter_tipo = ctk.CTkOptionMenu(
            ff, values=["Todos", "Ingreso", "Gasto"],
            fg_color=INPUT_BG, button_color=ACCENT, width=110
        )
        self.filter_tipo.grid(row=0, column=2, padx=(0, 12), pady=12)

        ctk.CTkLabel(ff, text="Desde:", text_color=TEXT2, font=ctk.CTkFont(size=11)
                     ).grid(row=0, column=3, padx=(0, 4), sticky="e")
        self.filter_desde = ctk.CTkEntry(ff, placeholder_text="DD/MM/YYYY",
                                          fg_color=INPUT_BG, width=110)
        self.filter_desde.grid(row=0, column=4, padx=(0, 12), pady=12)

        ctk.CTkLabel(ff, text="Hasta:", text_color=TEXT2, font=ctk.CTkFont(size=11)
                     ).grid(row=0, column=5, padx=(0, 4), sticky="e")
        self.filter_hasta = ctk.CTkEntry(ff, placeholder_text="DD/MM/YYYY",
                                          fg_color=INPUT_BG, width=110)
        self.filter_hasta.grid(row=0, column=6, padx=(0, 12), pady=12)

        ctk.CTkButton(
            ff, text="🔍 Filtrar", width=90,
            fg_color=ACCENT, hover_color="#1a4a7a",
            command=self._load_transactions
        ).grid(row=0, column=7, padx=(0, 8), pady=12)
        ctk.CTkButton(
            ff, text="✕ Limpiar", width=80,
            fg_color="transparent", hover_color=ACCENT, text_color=TEXT2, border_width=1,
            command=self._clear_filters
        ).grid(row=0, column=8, padx=(0, 15), pady=12)

        # ── Tabla ──
        table_outer = ctk.CTkFrame(body, fg_color=PANEL, corner_radius=12)
        table_outer.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        table_outer.grid_columnconfigure(0, weight=1)
        table_outer.grid_rowconfigure(1, weight=1)

        # Sub-header con conteo MEJORA #6
        self.count_label = ctk.CTkLabel(
            table_outer, text="",
            font=ctk.CTkFont(size=11), text_color=TEXT2
        )
        self.count_label.grid(row=0, column=0, padx=15, pady=(8, 0), sticky="e")

        # Encabezados
        thead = ctk.CTkFrame(table_outer, fg_color=ACCENT, corner_radius=0, height=36)
        thead.grid(row=1, column=0, sticky="ew")
        thead.grid_propagate(False)
        thead.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        for col, h in enumerate(["Fecha", "Tipo", "Categoría", "Descripción", "Monto", "Acciones"]):
            ctk.CTkLabel(
                thead, text=h,
                font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT
            ).grid(row=0, column=col, padx=10, pady=8, sticky="w")

        self.table_scroll = ctk.CTkScrollableFrame(
            table_outer, fg_color="transparent", corner_radius=0
        )
        self.table_scroll.grid(row=2, column=0, sticky="nsew")
        self.table_scroll.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.table_frame = self.table_scroll

    # ── Carga y render ─────────────────────────────────────────────────────

    def _get_filters(self):
        tipo_map = {"Todos": None, "Ingreso": "ingreso", "Gasto": "gasto"}
        tipo = tipo_map.get(self.filter_tipo.get())
        desde_str = self.filter_desde.get().strip()
        hasta_str = self.filter_hasta.get().strip()
        fd = fh = None
        if desde_str:
            ok, fd, _ = validate_fecha(desde_str)
            if not ok: fd = None
        if hasta_str:
            ok, fh, _ = validate_fecha(hasta_str)
            if not ok: fh = None
        return tipo, fd, fh

    def _load_transactions(self):
        for w in self.table_frame.winfo_children():
            w.destroy()

        tipo, fd, fh = self._get_filters()
        txs = self.tx_service.get_all(tipo=tipo, fecha_desde=fd, fecha_hasta=fh)

        # MEJORA #6: conteo y paginación
        total = len(txs)
        shown = min(total, PAGE_SIZE)
        self.count_label.configure(
            text=f"Mostrando {shown} de {total} transacciones"
        )
        txs = txs[:PAGE_SIZE]

        if not txs:
            ctk.CTkLabel(
                self.table_frame, text="No hay transacciones que mostrar.",
                text_color=TEXT2, font=ctk.CTkFont(size=13)
            ).grid(row=0, column=0, columnspan=6, pady=40)
            return

        for i, tx in enumerate(txs):
            d = tx.to_dict()
            icon       = "⬆️" if d["tipo"] == "ingreso" else "⬇️"
            color_monto = GREEN if d["tipo"] == "ingreso" else RED
            row_data = [
                (d["fecha"], TEXT),
                (f"{icon} {d['tipo'].capitalize()}", TEXT),
                (d["categoria_nombre"] or "—", TEXT),
                ((d["descripcion"] or "—")[:35], TEXT2),
                (f"${d['monto']:,.2f}", color_monto),
            ]
            for col, (val, clr) in enumerate(row_data):
                ctk.CTkLabel(
                    self.table_frame, text=val,
                    font=ctk.CTkFont(size=11), text_color=clr, anchor="w"
                ).grid(row=i, column=col, padx=10, pady=6, sticky="w")

            actions = ctk.CTkFrame(self.table_frame, fg_color="transparent")
            actions.grid(row=i, column=5, padx=5, pady=4, sticky="w")
            ctk.CTkButton(
                actions, text="✏️", width=32, height=28,
                fg_color=ACCENT, hover_color="#1a4a7a",
                command=lambda tid=tx.id: self._edit_transaction(tid)
            ).pack(side="left", padx=2)
            ctk.CTkButton(
                actions, text="🗑️", width=32, height=28,
                fg_color="#4a1020", hover_color=RED,
                command=lambda tid=tx.id: self._delete_transaction(tid)
            ).pack(side="left", padx=2)

    def _clear_filters(self):
        self.filter_tipo.set("Todos")
        self.filter_desde.delete(0, "end")
        self.filter_hasta.delete(0, "end")
        self._load_transactions()

    # ── Formulario (MEJORAS #3, #4, #5, #8) ──────────────────────────────

    def _open_form(self, tx_id: Optional[int] = None):
        self._editing_id = tx_id
        tx = self.tx_service.get_by_id(tx_id) if tx_id else None

        win = ctk.CTkToplevel(self)
        win.title("Nueva Transacción" if not tx else "Editar Transacción")
        win.geometry("440x540")
        win.grab_set()
        win.configure(fg_color=BG)
        win.resizable(False, False)

        # MEJORA #4: cerrar con Escape
        win.bind("<Escape>", lambda e: win.destroy())

        ctk.CTkLabel(
            win, text="💳 Nueva Transacción" if not tx else "✏️ Editar Transacción",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT
        ).pack(pady=(20, 10))

        form = ctk.CTkFrame(win, fg_color=PANEL, corner_radius=12)
        form.pack(fill="both", expand=True, padx=20, pady=10)
        form.grid_columnconfigure(0, weight=1)

        def lbl(text, row):
            ctk.CTkLabel(form, text=text, text_color=TEXT2,
                         font=ctk.CTkFont(size=11)
                         ).grid(row=row, column=0, padx=20, pady=(10, 2), sticky="w")

        # Tipo
        lbl("Tipo *", 0)
        tipo_var = ctk.StringVar(value=tx.tipo.capitalize() if tx else "Gasto")
        tipo_menu = ctk.CTkOptionMenu(
            form, values=["Gasto", "Ingreso"], variable=tipo_var,
            fg_color=INPUT_BG, button_color=ACCENT,
            command=lambda _: self._update_categories(cat_menu, tipo_var)
        )
        tipo_menu.grid(row=1, column=0, padx=20, pady=(0, 5), sticky="ew")

        # Monto
        lbl("Monto *", 2)
        monto_entry = ctk.CTkEntry(form, placeholder_text="Ej: 50000", fg_color=INPUT_BG)
        monto_entry.grid(row=3, column=0, padx=20, pady=(0, 5), sticky="ew")
        if tx:
            monto_entry.insert(0, str(tx.monto))

        # Fecha
        lbl("Fecha * (DD/MM/YYYY)", 4)
        fecha_entry = ctk.CTkEntry(
            form, placeholder_text=f"Ej: {date.today().strftime('%d/%m/%Y')}",
            fg_color=INPUT_BG
        )
        fecha_entry.grid(row=5, column=0, padx=20, pady=(0, 5), sticky="ew")
        if tx:
            fecha_entry.insert(0, tx.fecha.strftime("%d/%m/%Y"))
        else:
            fecha_entry.insert(0, date.today().strftime("%d/%m/%Y"))

        # Categoría
        lbl("Categoría *", 6)
        categories = self.cat_service.get_by_tipo(tipo_var.get().lower())
        cat_names = [c.nombre for c in categories]
        cat_menu = ctk.CTkOptionMenu(
            form, values=cat_names if cat_names else ["(sin categorías)"],
            fg_color=INPUT_BG, button_color=ACCENT
        )
        cat_menu.grid(row=7, column=0, padx=20, pady=(0, 5), sticky="ew")
        if tx:
            cat_menu.set(tx.categoria.nombre)
        self._cat_objects = categories

        # Descripción
        lbl("Descripción (opcional)", 8)
        desc_entry = ctk.CTkEntry(
            form, placeholder_text="Notas sobre la transacción", fg_color=INPUT_BG
        )
        desc_entry.grid(row=9, column=0, padx=20, pady=(0, 5), sticky="ew")
        if tx and tx.descripcion:
            desc_entry.insert(0, tx.descripcion)

        # MEJORA #3: error label con auto-clear
        error_lbl = ctk.CTkLabel(form, text="", text_color=RED, font=ctk.CTkFont(size=11))
        error_lbl.grid(row=10, column=0, padx=20, pady=(5, 0))

        # MEJORA #5: validación inline de fecha al salir del campo
        def _validate_fecha_inline(event=None):
            val = fecha_entry.get().strip()
            if val:
                ok, _, msg = validate_fecha(val)
                if not ok:
                    fecha_entry.configure(border_color=RED)
                    set_error(error_lbl, msg)
                else:
                    fecha_entry.configure(border_color=GREEN)
        fecha_entry.bind("<FocusOut>", _validate_fecha_inline)

        # MEJORA #5: validación inline de monto
        def _validate_monto_inline(event=None):
            val = monto_entry.get().strip()
            if val:
                ok, _, msg = validate_monto(val)
                monto_entry.configure(border_color=GREEN if ok else RED)
        monto_entry.bind("<FocusOut>", _validate_monto_inline)

        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(pady=15)

        def save():
            ok_m, monto, msg_m = validate_monto(monto_entry.get())
            ok_f, fecha, msg_f = validate_fecha(fecha_entry.get())
            if not ok_m:
                set_error(error_lbl, msg_m); return   # MEJORA #3
            if not ok_f:
                set_error(error_lbl, msg_f); return

            tipo = tipo_var.get().lower()
            cat_nombre = cat_menu.get()
            cat = next((c for c in self._cat_objects if c.nombre == cat_nombre), None)
            if not cat:
                set_error(error_lbl, "Selecciona una categoría válida."); return

            try:
                if tx:
                    self.tx_service.update(
                        tx.id, monto=monto, fecha=fecha, tipo=tipo,
                        categoria_id=cat.id, descripcion=desc_entry.get()
                    )
                    msg = "Transacción actualizada correctamente."
                else:
                    self.tx_service.create(
                        monto=monto, fecha=fecha, tipo=tipo,
                        categoria_id=cat.id, descripcion=desc_entry.get()
                    )
                    msg = f"Transacción de ${monto:,.0f} guardada."
                win.destroy()
                self._load_transactions()
                show_toast(self, msg, kind="success")  # MEJORA #8
            except ValueError as e:
                set_error(error_lbl, str(e))

        save_btn = ctk.CTkButton(
            btn_frame, text="💾 Guardar",
            fg_color=GREEN, hover_color="#27ae60", text_color="#000000",
            width=130, command=save
        )
        save_btn.pack(side="left", padx=8)
        ctk.CTkButton(
            btn_frame, text="Cancelar",
            fg_color="transparent", hover_color=ACCENT, border_width=1,
            width=100, command=win.destroy
        ).pack(side="left", padx=8)

        # MEJORA #4: Enter guarda, foco inicial en monto
        win.bind("<Return>", lambda e: save())
        monto_entry.focus_set()

    def _update_categories(self, cat_menu, tipo_var):
        tipo = tipo_var.get().lower()
        categories = self.cat_service.get_by_tipo(tipo)
        self._cat_objects = categories
        names = [c.nombre for c in categories]
        cat_menu.configure(values=names if names else ["(sin categorías)"])
        if names:
            cat_menu.set(names[0])

    def _edit_transaction(self, tx_id: int):
        self._open_form(tx_id=tx_id)

    def _delete_transaction(self, tx_id: int):
        tx = self.tx_service.get_by_id(tx_id)
        if not tx:
            return
        confirm = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar la transacción de ${tx.monto:,.2f} del {tx.fecha}?"
        )
        if confirm:
            try:
                self.tx_service.delete(tx_id)
                self._load_transactions()
                show_toast(self, "Transacción eliminada.", kind="info")  # MEJORA #8
            except ValueError as e:
                messagebox.showerror("Error", str(e))
