"""
Utilidades de validación para inputs de formularios.
Separadas de la UI para facilitar testing y reutilización.
"""

import re
from datetime import date, datetime
from typing import Tuple, Optional


# ─────────────────────────────────────────────
# MONTO
# ─────────────────────────────────────────────

def validate_monto(value: str) -> Tuple[bool, Optional[float], str]:
    """
    Valida que el string represente un monto monetario válido.
    Returns: (es_valido, valor_float, mensaje_error)
    """
    if value is None:
        return False, None, "El monto es obligatorio."

    value = value.strip().replace(",", ".")

    if not value:
        return False, None, "El monto es obligatorio."

    try:
        monto = float(value)
    except ValueError:
        return False, None, "El monto debe ser un número válido."

    if monto <= 0:
        return False, None, "El monto debe ser mayor a 0."

    if monto > 1_000_000_000:
        return False, None, "El monto es demasiado grande."

    return True, round(monto, 2), ""


# ─────────────────────────────────────────────
# FECHA
# ─────────────────────────────────────────────

def validate_fecha(value: str) -> Tuple[bool, Optional[date], str]:
    """
    Valida fechas en formato:
    - DD/MM/YYYY
    - YYYY-MM-DD
    - DD-MM-YYYY
    Returns: (es_valido, objeto_date, mensaje_error)
    """
    if value is None:
        return False, None, "La fecha es obligatoria."

    value = value.strip()

    if not value:
        return False, None, "La fecha es obligatoria."

    formatos = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]
    parsed = None

    for fmt in formatos:
        try:
            parsed = datetime.strptime(value, fmt).date()
            break
        except ValueError:
            continue

    if parsed is None:
        return False, None, "Formato inválido. Use DD/MM/YYYY."

    if parsed > date.today():
        return False, None, "La fecha no puede ser futura."

    return True, parsed, ""


# ─────────────────────────────────────────────
# NOMBRE
# ─────────────────────────────────────────────

def validate_nombre(value: str, max_len: int = 100) -> Tuple[bool, str, str]:
    """
    Valida nombres (categorías, inversiones, etc.)
    """
    if value is None:
        return False, "", "El nombre es obligatorio."

    value = value.strip()

    if not value:
        return False, "", "El nombre es obligatorio."

    if len(value) > max_len:
        return False, "", f"Máximo {max_len} caracteres."

    return True, value, ""


# ─────────────────────────────────────────────
# COLOR HEX
# ─────────────────────────────────────────────

def validate_color_hex(value: str) -> Tuple[bool, str, str]:
    """
    Valida que el valor sea un color hexadecimal válido (#RRGGBB)
    """
    if value is None:
        return False, "", "El color es obligatorio."

    value = value.strip()

    if re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
        return True, value.upper(), ""

    return False, "", "Color inválido. Usa formato #RRGGBB."