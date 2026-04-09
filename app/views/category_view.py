"""
Vista de Gestión de Categorías.
CRUD completo con selector de color y contador de transacciones.
"""

import customtkinter as ctk
from tkinter import messagebox, colorchooser
from typing import Callable

from sqlalchemy.orm import Session

from app.services.category_service import CategoryService
from app.utils.validators import validate_nombre, validate_color_hex

BG = "#1a1a2e"
PANEL = "#16213e"
ACCENT = "#0f3460"
GREEN = "#2ecc71"
RED = "#e74c3c"
TEXT = "#e0e0e0"
TEXT2 = "#a0a0b0"
INPUT_BG = "#0d1b2a"


class CategoryView(ctk.CTkFrame):
    def __init__(self, parent, session: Session, navigate: Callable):
        super().__init__(parent, fg_color=BG, corner_radius=0)
        self.session = session
        self.navigate = navigate
        self.cat_service = CategoryService(session)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_body()
        self._load_categories()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=0, height=60)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header, text="🏷️  Gestión de Categorías",
            font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT
        ).grid(row=0, column=0, padx=20, pady=15, sticky="w")

        ctk.CTkButton(
            header, text="+ Nueva Categoría", width=155,
            fg_color=GREEN, hover_color="#27ae60", text_color="#000000",
            command=self._open_form
        ).grid(row=0, column=2, padx=20, pady=15)

    def _build_body(self):
        body = ctk.CTkScrollableFrame(self, fg_color=BG, corner_radius=0)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure((0, 1), weight=1)
        self.body = body

    def _load_categories(self):
        for w in self.body.winfo_children():
            w.destroy()

        categories = self.cat_service.get_all()
        if not categories:
            ctk.CTkLabel(
                self.body, text="No hay categorías. Crea la primera con el botón de arriba.",
                text_color=TEXT2, font=ctk.CTkFont(size=13)
            ).grid(row=0, column=0, columnspan=2, pady=60)
            return

        # Separar por tipo
        gastos = [c for c in categories if c.tipo == "gasto"]
        ingresos = [c for c in categories if c.tipo == "ingreso"]

        for col, (tipo_label, icon, items) in enumerate([
            ("Gastos", "⬇️", gastos),
            ("Ingresos", "⬆️", ingresos),
        ]):
            section = ctk.CTkFrame(self.body, fg_color=PANEL, corner_radius=12)
            section.grid(row=0, column=col, padx=10, pady=15, sticky="nsew")
            section.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                section, text=f"{icon}  {tipo_label} ({len(items)})",
                font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT
            ).grid(row=0, column=0, padx=15, pady=(15, 10), sticky="w")

            if not items:
                ctk.CTkLabel(section, text="Sin categorías de este tipo.",
                             text_color=TEXT2, font=ctk.CTkFont(size=11)
                             ).grid(row=1, column=0, padx=15, pady=20)
                continue

            for i, cat in enumerate(items):
                self._render_category_row(section, cat, i + 1)

    def _render_category_row(self, parent, cat, row):
        row_frame = ctk.CTkFrame(parent, fg_color=BG, corner_radius=8, height=52)
        row_frame.grid(row=row, column=0, padx=10, pady=4, sticky="ew")
        row_frame.grid_columnconfigure(1, weight=1)
        row_frame.grid_propagate(False)

        # Chip de color
        color_btn = ctk.CTkButton(
            row_frame, text="", width=20, height=20,
            fg_color=cat.color, hover_color=cat.color,
            corner_radius=10, command=lambda c=cat: self._change_color(c)
        )


        
        color_btn.grid(row=0, column=0, padx=(12, 8), pady=16)

        # Nombre
        ctk.CTkLabel(
            row_frame, text=cat.nombre,
            font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT, anchor="w"
        ).grid(row=0, column=1, padx=0, pady=16, sticky="w")

        # Contador de transacciones
        tx_count = len(cat.transacciones)
        ctk.CTkLabel(
            row_frame, text=f"{tx_count} tx",
            font=ctk.CTkFont(size=10), text_color=TEXT2
        ).grid(row=0, column=2, padx=8)

        # Acciones
        actions = ctk.CTkFrame(row_frame, fg_color="transparent")
        actions.grid(row=0, column=3, padx=(0, 8))
        ctk.CTkButton(
            actions, text="✏️", width=30, height=28,
            fg_color=ACCENT, hover_color="#1a4a7a",
            command=lambda c=cat: self._open_form(c)
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            actions, text="🗑️", width=30, height=28,
            fg_color="#4a1020", hover_color=RED,
            command=lambda c=cat: self._delete_category(c)
        ).pack(side="left", padx=2)

    def _open_form(self, category=None):
        win = ctk.CTkToplevel(self)
        win.title("Nueva Categoría" if not category else "Editar Categoría")
        win.geometry("380x360")
        win.grab_set()
        win.configure(fg_color=BG)
        win.resizable(False, False)

        ctk.CTkLabel(
            win,
            text="🏷️ Nueva Categoría" if not category else "✏️ Editar Categoría",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT
        ).pack(pady=(20, 10))

        form = ctk.CTkFrame(win, fg_color=PANEL, corner_radius=12)
        form.pack(fill="both", expand=True, padx=20, pady=10)
        form.grid_columnconfigure(0, weight=1)

        def lbl(text, row):
            ctk.CTkLabel(form, text=text, text_color=TEXT2,
                         font=ctk.CTkFont(size=11)).grid(row=row, column=0, padx=20, pady=(12, 2), sticky="w")

        # Nombre
        lbl("Nombre *", 0)
        nombre_entry = ctk.CTkEntry(form, placeholder_text="Ej: Alimentación", fg_color=INPUT_BG)
        nombre_entry.grid(row=1, column=0, padx=20, pady=(0, 5), sticky="ew")
        if category:
            nombre_entry.insert(0, category.nombre)

        # Tipo
        lbl("Tipo *", 2)
        tipo_var = ctk.StringVar(value=category.tipo.capitalize() if category else "Gasto")
        tipo_menu = ctk.CTkOptionMenu(
            form, values=["Gasto", "Ingreso"], variable=tipo_var,
            fg_color=INPUT_BG, button_color=ACCENT
        )
        tipo_menu.grid(row=3, column=0, padx=20, pady=(0, 5), sticky="ew")

        # Color
        lbl("Color", 4)
        color_frame = ctk.CTkFrame(form, fg_color="transparent")
        color_frame.grid(row=5, column=0, padx=20, pady=(0, 5), sticky="ew")
        color_frame.grid_columnconfigure(0, weight=1)

        initial_color = category.color if category else "#4A90D9"
        color_var = ctk.StringVar(value=initial_color)
        color_entry = ctk.CTkEntry(color_frame, textvariable=color_var,
                                    fg_color=INPUT_BG, width=100)
        color_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        color_preview = ctk.CTkButton(
            color_frame, text="  ", width=40, height=30,
            fg_color=initial_color, hover_color=initial_color
        )
        color_preview.grid(row=0, column=1)

        def pick_color():
            chosen = colorchooser.askcolor(color=color_var.get(), title="Elegir color")
            if chosen[1]:
                color_var.set(chosen[1].upper())
                color_preview.configure(fg_color=chosen[1], hover_color=chosen[1])

        ctk.CTkButton(
            color_frame, text="🎨", width=36, height=30,
            fg_color=ACCENT, hover_color="#1a4a7a",
            command=pick_color
        ).grid(row=0, column=2, padx=(4, 0))

        error_lbl = ctk.CTkLabel(form, text="", text_color=RED, font=ctk.CTkFont(size=11))
        error_lbl.grid(row=6, column=0, padx=20, pady=(8, 0))

        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(pady=15)

        def save():
            ok_n, nombre, msg_n = validate_nombre(nombre_entry.get())
            if not ok_n:
                error_lbl.configure(text=msg_n); return
            ok_c, color, msg_c = validate_color_hex(color_var.get())
            if not ok_c:
                error_lbl.configure(text=msg_c); return
            tipo = tipo_var.get().lower()
            try:
                if category:
                    self.cat_service.update(category.id, nombre=nombre, tipo=tipo, color=color)
                else:
                    self.cat_service.create(nombre=nombre, tipo=tipo, color=color)
                win.destroy()
                self._load_categories()
            except ValueError as e:
                error_lbl.configure(text=str(e))

        ctk.CTkButton(btn_frame, text="💾 Guardar", fg_color=GREEN, hover_color="#27ae60",
                       text_color="#000000", width=130, command=save).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="Cancelar", fg_color="transparent",
                       hover_color=ACCENT, border_width=1, width=100,
                       command=win.destroy).pack(side="left", padx=8)

    def _change_color(self, category):
        chosen = colorchooser.askcolor(color=category.color, title="Cambiar color")
        if chosen[1]:
            try:
                self.cat_service.update(category.id, color=chosen[1].upper())
                self._load_categories()
            except ValueError as e:
                messagebox.showerror("Error", str(e))

    def _delete_category(self, category):
        confirm = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar la categoría '{category.nombre}'?\n"
            "Solo es posible si no tiene transacciones asociadas."
        )
        if confirm:
            try:
                self.cat_service.delete(category.id)
                self._load_categories()
            except ValueError as e:
                messagebox.showerror("No se puede eliminar", str(e))