"""
Helpers de UI reutilizables entre vistas.
- Toast de éxito / error
- Manejo de labels de error con auto-clear
- Tooltip simple hover
- Indicador de carga (overlay)
"""

import customtkinter as ctk
from typing import Optional

SUCCESS_COLOR = "#2ecc71"
ERROR_COLOR   = "#e74c3c"
INFO_COLOR    = "#3498db"
WARN_COLOR    = "#f39c12"

TEXT_DARK = "#0d1b2a"
PANEL     = "#16213e"


# ── Toast ──────────────────────────────────────────────────────────────────

def show_toast(
    root: ctk.CTk | ctk.CTkToplevel | ctk.CTkFrame,
    message: str,
    kind: str = "success",   # "success" | "error" | "info" | "warning"
    duration_ms: int = 2800,
) -> None:
    """
    Muestra una notificación flotante en la esquina inferior derecha.
    Se destruye automáticamente después de `duration_ms`.
    """
    color_map = {
        "success": SUCCESS_COLOR,
        "error":   ERROR_COLOR,
        "info":    INFO_COLOR,
        "warning": WARN_COLOR,
    }
    icon_map = {
        "success": "✅",
        "error":   "❌",
        "info":    "ℹ️",
        "warning": "⚠️",
    }

    # Buscar la ventana raíz para anclar el toast
    anchor = root
    while hasattr(anchor, 'master') and anchor.master is not None:
        anchor = anchor.master

    bg = color_map.get(kind, SUCCESS_COLOR)
    icon = icon_map.get(kind, "✅")

    toast = ctk.CTkFrame(anchor, fg_color=bg, corner_radius=10)
    ctk.CTkLabel(
        toast,
        text=f"  {icon}  {message}  ",
        font=ctk.CTkFont(size=12, weight="bold"),
        text_color=TEXT_DARK,
    ).pack(padx=8, pady=8)

    toast.place(relx=0.98, rely=0.97, anchor="se")
    toast.lift()

    # Animación de salida: fade out suave antes de destruir
    def _fade_out(alpha_step: int = 0):
        try:
            if alpha_step < 5:
                toast.after(60, lambda: _fade_out(alpha_step + 1))
            else:
                toast.destroy()
        except Exception:
            pass

    anchor.after(duration_ms, _fade_out)


# ── Error label con auto-clear ────────────────────────────────────────────

def set_error(label: ctk.CTkLabel, message: str, clear_after_ms: int = 4000) -> None:
    """
    Escribe un mensaje de error en el label y lo limpia automáticamente.
    """
    label.configure(text=f"⚠️  {message}")
    label._clear_job = label.after(clear_after_ms, lambda: label.configure(text=""))


def clear_error(label: ctk.CTkLabel) -> None:
    if hasattr(label, '_clear_job'):
        try:
            label.after_cancel(label._clear_job)
        except Exception:
            pass
    label.configure(text="")


# ── Tooltip ───────────────────────────────────────────────────────────────

class Tooltip:
    """
    Tooltip simple que aparece al hacer hover sobre un widget.
    Compatible con cualquier widget CTk / Tkinter.
    """

    def __init__(self, widget, text: str, delay_ms: int = 500):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._tip_window: Optional[ctk.CTkToplevel] = None
        self._job = None

        widget.bind("<Enter>", self._schedule_show)
        widget.bind("<Leave>", self._hide)
        widget.bind("<ButtonPress>", self._hide)

    def _schedule_show(self, event=None):
        self._cancel()
        self._job = self.widget.after(self.delay_ms, self._show)

    def _show(self):
        if self._tip_window:
            return
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() - 32

        self._tip_window = ctk.CTkToplevel(self.widget)
        self._tip_window.wm_overrideredirect(True)
        self._tip_window.wm_geometry(f"+{x}+{y}")
        self._tip_window.configure(fg_color="#2a2a4a")

        ctk.CTkLabel(
            self._tip_window,
            text=self.text,
            font=ctk.CTkFont(size=11),
            text_color="#e0e0e0",
            fg_color="#2a2a4a",
            corner_radius=6,
        ).pack(padx=8, pady=4)

    def _hide(self, event=None):
        self._cancel()
        if self._tip_window:
            try:
                self._tip_window.destroy()
            except Exception:
                pass
            self._tip_window = None

    def _cancel(self):
        if self._job:
            try:
                self.widget.after_cancel(self._job)
            except Exception:
                pass
            self._job = None


# ── Loading overlay ───────────────────────────────────────────────────────

class LoadingOverlay:
    """
    Overlay semitransparente con spinner de texto.
    Uso:
        overlay = LoadingOverlay(parent_frame)
        overlay.show("Cargando datos...")
        # ... operación ...
        overlay.hide()
    """

    def __init__(self, parent: ctk.CTkFrame):
        self.parent = parent
        self._frame: Optional[ctk.CTkFrame] = None
        self._label: Optional[ctk.CTkLabel] = None
        self._spin_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._spin_idx = 0
        self._spin_job = None

    def show(self, message: str = "Cargando...") -> None:
        if self._frame:
            return
        self._frame = ctk.CTkFrame(
            self.parent, fg_color="#1a1a2e", corner_radius=0
        )
        self._frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._frame.lift()

        self._label = ctk.CTkLabel(
            self._frame,
            text=f"⠋  {message}",
            font=ctk.CTkFont(size=14),
            text_color="#a0a0b0",
        )
        self._label.place(relx=0.5, rely=0.5, anchor="center")
        self._animate(message)

    def _animate(self, message: str) -> None:
        if not self._frame or not self._label:
            return
        char = self._spin_chars[self._spin_idx % len(self._spin_chars)]
        try:
            self._label.configure(text=f"{char}  {message}")
        except Exception:
            return
        self._spin_idx += 1
        self._spin_job = self.parent.after(80, lambda: self._animate(message))

    def hide(self) -> None:
        if self._spin_job:
            try:
                self.parent.after_cancel(self._spin_job)
            except Exception:
                pass
        if self._frame:
            try:
                self._frame.destroy()
            except Exception:
                pass
            self._frame = None
            self._label = None
