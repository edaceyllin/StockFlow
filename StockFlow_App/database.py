"""SQLite veri erişim katmanı.

Ürün satırları yalnızca ``product_from_row`` ile ``Product`` nesnesine çevrilir.
Bu sayede model/veritabanı alan sırası hiçbir yerde birbirinden kopmaz.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from models import Product


def _application_path() -> Path:
    """Uygulamanın çalıştığı dizini döndürür; Python betiği veya .exe fark etmez."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


APP_PATH = _application_path()
DB_PATH = APP_PATH / "database" / "stock.db"

PRODUCT_COLUMNS = (
    "barcode, product_name, category, brand, vehicle_model, purchase_price, "
    "sale_price, stock, oem_code, shelf_code, supplier, min_stock"
)


def _connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def product_from_row(row: sqlite3.Row) -> Product:
    return Product(
        barcode=row["barcode"], product_name=row["product_name"],
        category=row["category"] or "", brand=row["brand"] or "",
        vehicle_model=row["vehicle_model"] or "",
        purchase_price=float(row["purchase_price"] or 0),
        sale_price=float(row["sale_price"] or 0), stock=int(row["stock"] or 0),
        oem_code=row["oem_code"] or "", shelf_code=row["shelf_code"] or "",
        supplier=row["supplier"] or "", min_stock=int(row["min_stock"] or 5),
    )


def _add_column_if_missing(cursor: sqlite3.Cursor, column: str, definition: str) -> None:
    columns = {item[1] for item in cursor.execute("PRAGMA table_info(products)")}
    if column not in columns:
        cursor.execute(f"ALTER TABLE products ADD COLUMN {column} {definition}")


def create_database() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT NOT NULL UNIQUE,
                product_name TEXT NOT NULL,
                category TEXT DEFAULT '', brand TEXT DEFAULT '', vehicle_model TEXT DEFAULT '',
                purchase_price REAL DEFAULT 0, sale_price REAL DEFAULT 0, stock INTEGER DEFAULT 0,
                oem_code TEXT DEFAULT '', shelf_code TEXT DEFAULT '', supplier TEXT DEFAULT '',
                min_stock INTEGER DEFAULT 5
            )
        """)
        # Önceki sürümlerin veritabanlarını veri kaybetmeden güncelle.
        for name, definition in (
            ("oem_code", "TEXT DEFAULT ''"), ("shelf_code", "TEXT DEFAULT ''"),
            ("supplier", "TEXT DEFAULT ''"), ("min_stock", "INTEGER DEFAULT 5"),
        ):
            _add_column_if_missing(cursor, name, definition)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_date TEXT NOT NULL, barcode TEXT NOT NULL,
                product_name TEXT DEFAULT '', quantity INTEGER NOT NULL,
                sale_price REAL NOT NULL
            )
        """)
        sale_columns = {item[1] for item in cursor.execute("PRAGMA table_info(sales)")}
        if "product_name" not in sale_columns:
            cursor.execute("ALTER TABLE sales ADD COLUMN product_name TEXT DEFAULT ''")


def save_product(product: Product) -> bool:
    """Yeni ürün ekler; aynı barkod varsa False döndürür."""
    with _connection() as conn:
        try:
            conn.execute(
                f"INSERT INTO products ({PRODUCT_COLUMNS}) VALUES ({','.join('?' * 12)})",
                _product_values(product),
            )
            return True
        except sqlite3.IntegrityError:
            return False


def _product_values(product: Product) -> tuple:
    return (product.barcode, product.product_name, product.category, product.brand,
            product.vehicle_model, product.purchase_price, product.sale_price, product.stock,
            product.oem_code, product.shelf_code, product.supplier, product.min_stock)


def get_products() -> list[Product]:
    with _connection() as conn:
        rows = conn.execute(f"SELECT {PRODUCT_COLUMNS} FROM products ORDER BY product_name COLLATE NOCASE").fetchall()
    return [product_from_row(row) for row in rows]


def update_product(product: Product) -> bool:
    with _connection() as conn:
        result = conn.execute("""
            UPDATE products SET product_name=?, category=?, brand=?, vehicle_model=?,
                purchase_price=?, sale_price=?, stock=?, oem_code=?, shelf_code=?,
                supplier=?, min_stock=? WHERE barcode=?
        """, (*_product_values(product)[1:], product.barcode))
    return result.rowcount > 0


def delete_product(barcode: str) -> bool:
    with _connection() as conn:
        result = conn.execute("DELETE FROM products WHERE barcode = ?", (barcode,))
    return result.rowcount > 0


def get_product_by_barcode(barcode: str) -> Product | None:
    with _connection() as conn:
        row = conn.execute(f"SELECT {PRODUCT_COLUMNS} FROM products WHERE barcode = ?", (barcode,)).fetchone()
    return product_from_row(row) if row else None


def increase_stock(barcode: str, amount: int) -> bool:
    if amount <= 0:
        raise ValueError("Stok artış miktarı sıfırdan büyük olmalıdır.")
    with _connection() as conn:
        result = conn.execute("UPDATE products SET stock = stock + ? WHERE barcode = ?", (amount, barcode))
    return result.rowcount > 0


def record_sale(items: list[tuple[Product, int]]) -> None:
    """Satışı tek işlemde kaydeder; stok yetersizse hiçbir satırı değiştirmez."""
    with _connection() as conn:
        cursor = conn.cursor()
        for product, quantity in items:
            row = cursor.execute("SELECT stock FROM products WHERE barcode = ?", (product.barcode,)).fetchone()
            if row is None or row["stock"] < quantity:
                raise ValueError(f"{product.product_name} için yeterli stok yok.")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for product, quantity in items:
            cursor.execute("""INSERT INTO sales (sale_date, barcode, product_name, quantity, sale_price)
                              VALUES (?, ?, ?, ?, ?)""",
                           (now, product.barcode, product.product_name, quantity, product.sale_price))
            cursor.execute("UPDATE products SET stock = stock - ? WHERE barcode = ?", (quantity, product.barcode))


def get_sales() -> list[sqlite3.Row]:
    with _connection() as conn:
        return conn.execute("""
            SELECT id, sale_date, barcode, product_name, quantity, sale_price,
                   quantity * sale_price AS total
            FROM sales ORDER BY id DESC
        """).fetchall()


def get_dashboard_stats() -> dict:
    with _connection() as conn:
        total_products, total_stock, total_value = conn.execute("""
            SELECT COUNT(*), COALESCE(SUM(stock), 0),
                   COALESCE(SUM(purchase_price * stock), 0) FROM products
        """).fetchone()
        low_stock_count = conn.execute("SELECT COUNT(*) FROM products WHERE stock <= min_stock").fetchone()[0]
    return {"total_products": total_products, "total_stock": total_stock,
            "total_value": total_value, "low_stock_count": low_stock_count}


def backup_database(destination_path: str | os.PathLike) -> bool:
    try:
        shutil.copy2(DB_PATH, destination_path)
        return True
    except OSError:
        return False


create_database()
