"""
Utilidades para generación de gráficos Matplotlib.
Cada función recibe datos procesados y retorna una Figure lista para embeber en Tkinter.
"""

from typing import List, Dict
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
import matplotlib.ticker as mticker


# ── Estilo ─────────────────────────────────────────────────────────────
BG_COLOR = "#1a1a2e"
PANEL_COLOR = "#16213e"
TEXT_COLOR = "#e0e0e0"
ACCENT_GREEN = "#2ecc71"
ACCENT_RED = "#e74c3c"
ACCENT_BLUE = "#3498db"
GRID_COLOR = "#2a2a4a"


def _apply_dark_style(fig: Figure, ax) -> None:
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(PANEL_COLOR)
    ax.tick_params(colors=TEXT_COLOR, labelsize=9)
    ax.xaxis.label.set_color(TEXT_COLOR)
    ax.yaxis.label.set_color(TEXT_COLOR)
    ax.title.set_color(TEXT_COLOR)

    for spine in ax.spines.values():
        spine.set_edgecolor(GRID_COLOR)

    ax.grid(color=GRID_COLOR, linestyle="--", linewidth=0.5, alpha=0.7)


# ── Gráfico 1: Dona ────────────────────────────────────────────────────

def chart_gastos_por_categoria(data: List[Dict], width=5, height=4) -> Figure:
    fig, ax = plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(BG_COLOR)

    if not data:
        ax.set_facecolor(PANEL_COLOR)
        ax.text(0.5, 0.5, "Sin datos disponibles",
                ha="center", va="center", color=TEXT_COLOR)
        ax.axis("off")
        return fig

    labels = [d["categoria"] for d in data]
    values = [float(d["total"]) for d in data]   # ← FIX importante
    colors = [d["color"] for d in data]

    total = sum(values)

    wedges, _, autotexts = ax.pie(
        values,
        colors=colors,
        autopct=lambda p: f"{p:.1f}%" if p > 3 else "",
        startangle=90,
        pctdistance=0.75,
        wedgeprops={"width": 0.6, "edgecolor": BG_COLOR},
    )

    for t in autotexts:
        t.set_color(TEXT_COLOR)

    legend_labels = [f"{l}  ${v:,.0f}" for l, v in zip(labels, values)]

    ax.legend(
        wedges, legend_labels,
        loc="center left",
        bbox_to_anchor=(1.0, 0.5),
        fontsize=8,
        labelcolor=TEXT_COLOR,
        facecolor=PANEL_COLOR,
        edgecolor=GRID_COLOR,
    )

    ax.set_title(f"Total: ${total:,.2f}", color=TEXT_COLOR)
    fig.tight_layout()
    return fig


# ── Gráfico 2: Evolución ───────────────────────────────────────────────

def chart_evolucion_mensual(data: List[Dict], width=7, height=4) -> Figure:
    fig, ax = plt.subplots(figsize=(width, height))
    _apply_dark_style(fig, ax)

    if not data:
        ax.text(0.5, 0.5, "Sin datos disponibles",
                ha="center", va="center", color=TEXT_COLOR)
        return fig

    periodos = [d["periodo"] for d in data]
    ingresos = [float(d["ingreso"]) for d in data]  # ← FIX
    gastos = [float(d["gasto"]) for d in data]      # ← FIX
    balances = [float(d["balance"]) for d in data]  # ← FIX

    x = range(len(periodos))
    w = 0.35

    ax.bar([i - w/2 for i in x], ingresos, w, color=ACCENT_GREEN, label="Ingresos")
    ax.bar([i + w/2 for i in x], gastos, w, color=ACCENT_RED, label="Gastos")

    ax2 = ax.twinx()
    ax2.plot(list(x), balances, color=ACCENT_BLUE, marker="o", label="Balance")

    ax.set_xticks(list(x))
    ax.set_xticklabels(periodos, rotation=45, ha="right")

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))

    handles = [
        mpatches.Patch(color=ACCENT_GREEN, label="Ingresos"),
        mpatches.Patch(color=ACCENT_RED, label="Gastos"),
        plt.Line2D([0], [0], color=ACCENT_BLUE, marker="o", label="Balance"),
    ]

    ax.legend(handles=handles, fontsize=8)
    fig.tight_layout()
    return fig


# ── Gráfico 3: Inversiones ─────────────────────────────────────────────

def chart_portafolio_inversiones(data: List[Dict], width=5, height=4) -> Figure:
    fig, ax = plt.subplots(figsize=(width, height))
    _apply_dark_style(fig, ax)

    if not data:
        ax.text(0.5, 0.5, "Sin inversiones",
                ha="center", va="center", color=TEXT_COLOR)
        return fig

    nombres = [d["nombre"][:18] for d in data]
    iniciales = [float(d["monto_inicial"]) for d in data]  # ← FIX
    actuales = [float(d["monto_actual"]) for d in data]    # ← FIX

    y = range(len(nombres))

    ax.barh([i + 0.2 for i in y], iniciales, 0.35, label="Inicial", color="#5DADE2")
    ax.barh(
        [i - 0.2 for i in y],
        actuales,
        0.35,
        label="Actual",
        color=[ACCENT_GREEN if a >= i else ACCENT_RED for a, i in zip(actuales, iniciales)],
    )

    ax.set_yticks(list(y))
    ax.set_yticklabels(nombres)

    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))

    ax.legend()
    fig.tight_layout()
    return fig