"""
Servicio de transacciones.
Maneja creación, consulta, edición y eliminación de transacciones.
También provee métodos de agregación para los gráficos del dashboard.
"""

from datetime import date, datetime
from typing import List, Optional, Dict, Tuple

from sqlalchemy import func, extract
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.category import Category
from app.database.connection import get_session


class TransactionService:
    """CRUD y consultas analíticas de transacciones."""

    def __init__(self, session: Optional[Session] = None):
        self._session = session
        self._owns_session = session is None

    @property
    def session(self) -> Session:
        if self._session is None:
            self._session = get_session()
        return self._session

    def close(self):
        if self._owns_session and self._session:
            self._session.close()
            self._session = None

    # ── Creación ─────────────────────────────────────────────────────────────

    def create(
        self,
        monto: float,
        fecha: date,
        tipo: str,
        categoria_id: int,
        descripcion: Optional[str] = None,
    ) -> Transaction:
        """Crea y persiste una nueva transacción con validación completa."""
        from decimal import Decimal
        monto = Decimal(monto)
        if monto <= 0:
            raise ValueError("El monto debe ser mayor a 0.")
        if tipo not in ("gasto", "ingreso"):
            raise ValueError("El tipo debe ser 'gasto' o 'ingreso'.")
        if not isinstance(fecha, date):
            raise ValueError("La fecha no es válida.")
        if fecha > date.today():
            raise ValueError("La fecha no puede ser futura.")

        # Verificar que la categoría existe y el tipo coincide
        from app.services.category_service import CategoryService
        cat_service = CategoryService(self.session)
        category = cat_service.get_by_id(categoria_id)
        if not category:
            raise ValueError(f"Categoría con id={categoria_id} no encontrada.")
        if category.tipo != tipo:
            raise ValueError(
                f"La categoría '{category.nombre}' es de tipo '{category.tipo}', "
                f"no '{tipo}'."
            )

        tx = Transaction(
            monto=monto,
            fecha=fecha,
            tipo=tipo,
            categoria_id=categoria_id,
            descripcion=descripcion.strip() if descripcion else None,
        )
        self.session.add(tx)
        self.session.commit()
        return tx

    # ── Lectura ──────────────────────────────────────────────────────────────

    def get_all(
        self,
        tipo: Optional[str] = None,
        categoria_id: Optional[int] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        limit: Optional[int] = None,
    ) -> List[Transaction]:
        """Consulta transacciones con filtros opcionales."""
        q = self.session.query(Transaction)
        if tipo:
            q = q.filter(Transaction.tipo == tipo)
        if categoria_id:
            q = q.filter(Transaction.categoria_id == categoria_id)
        if fecha_desde:
            q = q.filter(Transaction.fecha >= fecha_desde)
        if fecha_hasta:
            q = q.filter(Transaction.fecha <= fecha_hasta)
        q = q.order_by(Transaction.fecha.desc(), Transaction.id.desc())
        if limit:
            q = q.limit(limit)
        return q.all()

    def get_by_id(self, tx_id: int) -> Optional[Transaction]:
        return self.session.query(Transaction).filter(Transaction.id == tx_id).first()

    # ── Actualización ────────────────────────────────────────────────────────

    def update(
            
        self,
        tx_id: int,
        monto: Optional[float] = None,
        fecha: Optional[date] = None,
        tipo: Optional[str] = None,
        categoria_id: Optional[int] = None,
        descripcion: Optional[str] = None,
    ) -> Transaction:
        tx = self.get_by_id(tx_id)
        if not tx:
            raise ValueError(f"Transacción con id={tx_id} no encontrada.")

        if monto is not None:
            if float(monto) <= 0:
                raise ValueError("El monto debe ser mayor a 0.")
            tx.monto = float(monto)
        if fecha is not None:
            tx.fecha = fecha
        if tipo is not None:
            tx.tipo = tipo
        if categoria_id is not None:
            tx.categoria_id = categoria_id
        if descripcion is not None:
            tx.descripcion = descripcion.strip() or None

        self.session.commit()
        return tx
    
        from app.services.category_service import CategoryService

        cat_service = CategoryService(self.session)

        if categoria_id is not None:
            category = cat_service.get_by_id(categoria_id)
            if not category:
                raise ValueError("Categoría no encontrada.")

            if tipo is not None and category.tipo != tipo:
                raise ValueError("Tipo y categoría no coinciden.")

            tx.categoria_id = categoria_id

    # ── Eliminación ──────────────────────────────────────────────────────────

    def delete(self, tx_id: int) -> None:
        tx = self.get_by_id(tx_id)
        if not tx:
            raise ValueError(f"Transacción con id={tx_id} no encontrada.")
        self.session.delete(tx)
        self.session.commit()

    # ── Analítica / Agregaciones ─────────────────────────────────────────────

    def get_totales(
        self,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
    ) -> Dict[str, float]:
        """Retorna totales de ingresos, gastos y balance neto."""
        q = self.session.query(
            Transaction.tipo,
            func.sum(Transaction.monto).label("total"),
        )
        if fecha_desde:
            q = q.filter(Transaction.fecha >= fecha_desde)
        if fecha_hasta:
            q = q.filter(Transaction.fecha <= fecha_hasta)
        rows = q.group_by(Transaction.tipo).all()

        totales = {"ingreso": 0.0, "gasto": 0.0}
        for tipo, total in rows:
            totales[tipo] = float(total or 0)
        totales["balance"] = totales["ingreso"] - totales["gasto"]
        return totales

    def get_gastos_por_categoria(
        self,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
    ) -> List[Dict]:
        """Agrega gastos por categoría para el gráfico de torta."""
        q = (
            self.session.query(
                Category.nombre,
                Category.color,
                func.sum(Transaction.monto).label("total"),
            )
            .join(Category, Transaction.categoria_id == Category.id)
            .filter(Transaction.tipo == "gasto")
        )
        if fecha_desde:
            q = q.filter(Transaction.fecha >= fecha_desde)
        if fecha_hasta:
            q = q.filter(Transaction.fecha <= fecha_hasta)
        rows = q.group_by(Category.id).order_by(func.sum(Transaction.monto).desc()).all()

        return [
            {"categoria": row.nombre, "color": row.color, "total": float(row.total)}
            for row in rows
        ]

    def get_evolucion_mensual(
        self,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
    ) -> List[Dict]:
        """
        Retorna ingresos y gastos agrupados por mes.
        Usado para el gráfico de líneas del dashboard.
        """
        q = (
            self.session.query(
                extract("year", Transaction.fecha).label("anio"),
                extract("month", Transaction.fecha).label("mes"),
                Transaction.tipo,
                func.sum(Transaction.monto).label("total"),
            )
        )
        if fecha_desde:
            q = q.filter(Transaction.fecha >= fecha_desde)
        if fecha_hasta:
            q = q.filter(Transaction.fecha <= fecha_hasta)
        rows = (
            q.group_by("anio", "mes", Transaction.tipo)
            .order_by("anio", "mes")
            .all()
        )

        # Pivotear a formato {periodo: {ingreso: X, gasto: Y}}
        pivot: Dict[str, Dict] = {}
        for anio, mes, tipo, total in rows:
            key = f"{int(anio)}-{int(mes):02d}"
            if key not in pivot:
                pivot[key] = {"periodo": key, "ingreso": 0.0, "gasto": 0.0}
            pivot[key][tipo] = float(total or 0)

        result = sorted(pivot.values(), key=lambda x: x["periodo"])
        # Agregar balance mensual
        for item in result:
            item["balance"] = item["ingreso"] - item["gasto"]
        return result