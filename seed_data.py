"""
Script de seed data para poblar la base de datos con datos de prueba.
Ejecutar una sola vez antes de usar la aplicación por primera vez:

    python seed_data.py
"""

import sys
from pathlib import Path
from datetime import date, timedelta
import random

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database.connection import init_db, get_session
from app.services.category_service import CategoryService
from app.services.transaction_service import TransactionService
from app.services.investment_service import InvestmentService


def seed():
    print("🌱 Inicializando base de datos...")
    init_db()
    session = get_session()

    cat_svc = CategoryService(session)
    tx_svc  = TransactionService(session)
    inv_svc = InvestmentService(session)

    # ── Categorías de gastos ──────────────────────────────────────────────
    print("📂 Creando categorías...")
    gastos_cats = [
        ("Alimentación",    "#E74C3C"),
        ("Transporte",      "#E67E22"),
        ("Vivienda",        "#8E44AD"),
        ("Salud",           "#16A085"),
        ("Entretenimiento", "#2980B9"),
        ("Educación",       "#27AE60"),
        ("Ropa",            "#D35400"),
        ("Servicios",       "#7F8C8D"),
    ]
    ingresos_cats = [
        ("Salario",         "#2ECC71"),
        ("Freelance",       "#1ABC9C"),
        ("Inversiones",     "#F1C40F"),
        ("Otros ingresos",  "#3498DB"),
    ]

    cat_ids_gasto  = {}
    cat_ids_ingreso = {}

    for nombre, color in gastos_cats:
        try:
            c = cat_svc.create(nombre=nombre, tipo="gasto", color=color)
            cat_ids_gasto[nombre] = c.id
        except ValueError:
            existing = next(c for c in cat_svc.get_by_tipo("gasto") if c.nombre == nombre)
            cat_ids_gasto[nombre] = existing.id

    for nombre, color in ingresos_cats:
        try:
            c = cat_svc.create(nombre=nombre, tipo="ingreso", color=color)
            cat_ids_ingreso[nombre] = c.id
        except ValueError:
            existing = next(c for c in cat_svc.get_by_tipo("ingreso") if c.nombre == nombre)
            cat_ids_ingreso[nombre] = existing.id

    # ── Transacciones: últimos 6 meses ───────────────────────────────────
    print("💳 Generando transacciones (6 meses)...")
    today = date.today()

    # Ingresos mensuales fijos
    ingresos_fijos = [
        ("Salario",          4_500_000, "Salario mensual empresa"),
        ("Freelance",          800_000, "Proyecto diseño web"),
    ]

    # Gastos recurrentes mensuales
    gastos_recurrentes = [
        ("Vivienda",         1_200_000, "Arriendo"),
        ("Servicios",          180_000, "Internet + luz + agua"),
        ("Alimentación",       600_000, "Mercado mensual"),
        ("Transporte",         180_000, "Transporte público"),
    ]

    # Gastos variables aleatorios
    gastos_variables = [
        ("Alimentación",  (15_000, 80_000),  "Restaurante"),
        ("Entretenimiento",(20_000, 150_000), "Cine / salidas"),
        ("Salud",          (30_000, 200_000), "Consulta médica"),
        ("Ropa",           (50_000, 300_000), "Ropa y accesorios"),
        ("Educación",      (80_000, 400_000), "Curso online"),
    ]

    for months_back in range(5, -1, -1):
        # Calcular fecha del mes
        target_month = today.month - months_back
        target_year  = today.year
        while target_month <= 0:
            target_month += 12
            target_year  -= 1

        # Ingresos fijos el día 1 y 15
        for cat_nombre, monto, desc in ingresos_fijos:
            try:
                tx_svc.create(
                    monto=monto + random.randint(-50_000, 100_000),
                    fecha=date(target_year, target_month, 1),
                    tipo="ingreso",
                    categoria_id=cat_ids_ingreso[cat_nombre],
                    descripcion=desc,
                )
            except Exception:
                pass

        # Gastos recurrentes
        for cat_nombre, monto, desc in gastos_recurrentes:
            day = random.randint(1, 5)
            try:
                tx_svc.create(
                    monto=monto + random.randint(-30_000, 30_000),
                    fecha=date(target_year, target_month, day),
                    tipo="gasto",
                    categoria_id=cat_ids_gasto[cat_nombre],
                    descripcion=desc,
                )
            except Exception:
                pass

        # Gastos variables (3-7 por mes)
        for _ in range(random.randint(3, 7)):
            cat_nombre, (min_m, max_m), desc = random.choice(gastos_variables)
            day = random.randint(1, 28)
            try:
                tx_svc.create(
                    monto=random.randint(min_m // 1000, max_m // 1000) * 1000,
                    fecha=date(target_year, target_month, day),
                    tipo="gasto",
                    categoria_id=cat_ids_gasto[cat_nombre],
                    descripcion=desc,
                )
            except Exception:
                pass

    # ── Inversiones ───────────────────────────────────────────────────────
    print("📈 Creando inversiones...")
    inversiones = [
        {
            "nombre": "Fondo de Emergencia",
            "tipo": "ahorro",
            "monto_inicial": 5_000_000,
            "monto_actual":  5_850_000,
            "fecha_inicio":  date(today.year, 1, 1),
            "notas": "Meta: 3 meses de gastos",
        },
        {
            "nombre": "ETF S&P 500",
            "tipo": "acciones",
            "monto_inicial": 3_000_000,
            "monto_actual":  3_420_000,
            "fecha_inicio":  date(today.year - 1, 6, 15),
            "notas": "Inversión a largo plazo — no tocar",
        },
        {
            "nombre": "CDT Bancolombia",
            "tipo": "bonos",
            "monto_inicial": 2_000_000,
            "monto_actual":  2_180_000,
            "fecha_inicio":  date(today.year, 3, 1),
            "notas": "Vencimiento 12 meses, tasa EA 9%",
        },
        {
            "nombre": "Bitcoin",
            "tipo": "cripto",
            "monto_inicial": 1_000_000,
            "monto_actual":  870_000,
            "fecha_inicio":  date(today.year, 2, 10),
            "notas": "Posición especulativa — alto riesgo",
        },
    ]

    for inv_data in inversiones:
        try:
            inv_svc.create(**inv_data)
        except Exception as e:
            print(f"  ⚠ Inversión ya existe o error: {e}")

    session.close()
    print("\n✅ Seed completado exitosamente.")
    print("   Ejecuta: python app/main.py")


if __name__ == "__main__":
    seed()
