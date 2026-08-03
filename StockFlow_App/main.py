"""StockFlow ERP Lite - uygulama giriş noktası."""

import sys

from PyQt6.QtWidgets import QApplication

from gui import StockApp
from license import is_license_valid
from license_window import LicenseWindow


if __name__ == "__main__":
    app = QApplication.instance() or QApplication([])

    if not is_license_valid():
        license_window = LicenseWindow()
        license_window.show()
        sys.exit(app.exec())

    window = StockApp()
    window.show()

    sys.exit(app.exec())