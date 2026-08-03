from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QFileDialog,
    QMessageBox,
)

from license import get_machine_id, install_license, LicenseError


class LicenseWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("StockFlow ERP Lite - Lisans Gerekli")
        self.setFixedSize(400, 250)

        layout = QVBoxLayout()

        title = QLabel("StockFlow ERP Lite\nLisans Gerekli")
        title.setStyleSheet("font-size:18px;")

        self.machine_label = QLabel(
            f"Machine ID:\n{get_machine_id()}"
        )

        self.select_button = QPushButton("Lisans Dosyası Seç")
        self.select_button.clicked.connect(self.select_license)

        self.exit_button = QPushButton("Çıkış")
        self.exit_button.clicked.connect(self.close)

        layout.addWidget(title)
        layout.addWidget(self.machine_label)
        layout.addWidget(self.select_button)
        layout.addWidget(self.exit_button)

        self.setLayout(layout)

    def select_license(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "license.dat seç",
            "",
            "License Files (*.dat)"
        )

        if path:
            try:
                install_license(path)

                QMessageBox.information(
                    self,
                    "Başarılı",
                    "Lisans aktif edildi."
                )

                self.close()

            except LicenseError as e:
                QMessageBox.warning(
                    self,
                    "Lisans Hatası",
                    str(e)
                )