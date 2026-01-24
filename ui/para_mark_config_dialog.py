from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton,
    QListWidget, QGroupBox
)


class ParaMarkConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Para & Mark Config File")
        self.resize(780, 460)

        # Match legacy dialog behavior
        self.setWindowFlags(
            Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint
        )

        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("""
            QDialog {
                background: #f7f7f7;
                font-size: 13px;
            }

            QLabel {
                color: #2b2b2b;
            }

            QLineEdit {
                height: 28px;
                padding: 4px 6px;
                border: 1px solid #bdbdbd;
                border-radius: 4px;
                background: white;
            }

            QListWidget {
                border: 1px solid #bdbdbd;
                border-radius: 4px;
                background: white;
            }

            QGroupBox {
                border: 1px solid #cfcfcf;
                border-radius: 6px;
                margin-top: 14px;
                padding-top: 10px;
                font-weight: 600;
                color: #333;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                padding: 0 6px;
                background: #f7f7f7;
            }

            QPushButton {
                height: 28px;
                min-width: 70px;
                border-radius: 4px;
                background: #e6e6e6;
                border: 1px solid #bdbdbd;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #dcdcdc;
            }
        """)

        main = QVBoxLayout(self)
        main.setContentsMargins(16, 16, 16, 16)
        main.setSpacing(12)

        # ================= Panels =================
        panels = QHBoxLayout()
        panels.setSpacing(14)

        # ---------- PARA FILE ----------
        grp_para = QGroupBox("PARA FILE")
        para_layout = QGridLayout(grp_para)
        para_layout.setHorizontalSpacing(10)
        para_layout.setVerticalSpacing(8)

        para_layout.addWidget(QLabel("Scan No"), 0, 0)
        self.para_scan_no = QLineEdit()
        para_layout.addWidget(self.para_scan_no, 0, 1)

        btn_para_add = QPushButton("Add")
        para_layout.addWidget(btn_para_add, 0, 2, 2, 1)

        para_layout.addWidget(QLabel("Config Name"), 1, 0)
        self.para_config_name = QLineEdit()
        para_layout.addWidget(self.para_config_name, 1, 1)

        self.para_list = QListWidget()
        para_layout.addWidget(self.para_list, 2, 0, 1, 2)

        btn_para_remove = QPushButton("Remove")
        para_layout.addWidget(btn_para_remove, 2, 2, Qt.AlignTop)

        panels.addWidget(grp_para)

        # ---------- MARK FILE ----------
        grp_mark = QGroupBox("MARK FILE")
        mark_layout = QGridLayout(grp_mark)
        mark_layout.setHorizontalSpacing(10)
        mark_layout.setVerticalSpacing(8)

        mark_layout.addWidget(QLabel("Scan No"), 0, 0)
        self.mark_scan_no = QLineEdit()
        mark_layout.addWidget(self.mark_scan_no, 0, 1)

        btn_mark_add = QPushButton("Add")
        mark_layout.addWidget(btn_mark_add, 0, 2, 2, 1)

        mark_layout.addWidget(QLabel("Mark Symbol"), 1, 0)
        self.mark_symbol = QLineEdit()
        mark_layout.addWidget(self.mark_symbol, 1, 1)

        self.mark_list = QListWidget()
        mark_layout.addWidget(self.mark_list, 2, 0, 1, 2)

        btn_mark_remove = QPushButton("Remove")
        mark_layout.addWidget(btn_mark_remove, 2, 2, Qt.AlignTop)

        panels.addWidget(grp_mark)

        main.addLayout(panels)

        # ================= Bottom Button =================
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_close = QPushButton("Close")
        btn_close.setFixedWidth(90)
        btn_close.clicked.connect(self.close)

        btn_row.addWidget(btn_close)
        main.addLayout(btn_row)
