"""StockFlow'un ürün veri modeli."""

from dataclasses import dataclass


@dataclass(slots=True)
class Product:
    barcode: str
    product_name: str
    category: str = ""
    brand: str = ""
    vehicle_model: str = ""
    purchase_price: float = 0.0
    sale_price: float = 0.0
    stock: int = 0
    oem_code: str = ""
    shelf_code: str = ""
    supplier: str = ""
    min_stock: int = 5

    def decrease_stock(self, amount: int = 1) -> None:
        self.stock = max(0, self.stock - amount)

    def increase_stock(self, amount: int = 1) -> None:
        self.stock += amount
