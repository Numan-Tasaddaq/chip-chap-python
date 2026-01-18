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
        main = QVBoxLayout(self)
        main.setSpacing(10)

        # ================= Main Two Panels =================
        panels = QHBoxLayout()
        panels.setSpacing(12)

        # ---------- PARA FILE ----------
        grp_para = QGroupBox("PARA FILE")
        para_layout = QGridLayout(grp_para)
        para_layout.setHorizontalSpacing(10)
        para_layout.setVerticalSpacing(8)

        para_layout.addWidget(QLabel("Scan No:"), 0, 0)
        self.para_scan_no = QLineEdit()
        para_layout.addWidget(self.para_scan_no, 0, 1)

        btn_para_add = QPushButton("Add")
        btn_para_add.setFixedWidth(70)
        para_layout.addWidget(btn_para_add, 0, 2, 2, 1)

        para_layout.addWidget(QLabel("Config Name:"), 1, 0)
        self.para_config_name = QLineEdit()
        para_layout.addWidget(self.para_config_name, 1, 1)

        self.para_list = QListWidget()
        para_layout.addWidget(self.para_list, 2, 0, 1, 2)

        btn_para_remove = QPushButton("Remove")
        btn_para_remove.setFixedWidth(70)
        para_layout.addWidget(btn_para_remove, 2, 2, Qt.AlignTop)

        panels.addWidget(grp_para)

        # ---------- MARK FILE ----------
        grp_mark = QGroupBox("MARK FILE")
        mark_layout = QGridLayout(grp_mark)
        mark_layout.setHorizontalSpacing(10)
        mark_layout.setVerticalSpacing(8)

        mark_layout.addWidget(QLabel("Scan No:"), 0, 0)
        self.mark_scan_no = QLineEdit()
        mark_layout.addWidget(self.mark_scan_no, 0, 1)

        btn_mark_add = QPushButton("Add")
        btn_mark_add.setFixedWidth(70)
        mark_layout.addWidget(btn_mark_add, 0, 2, 2, 1)

        mark_layout.addWidget(QLabel("Mark Symbol:"), 1, 0)
        self.mark_symbol = QLineEdit()
        mark_layout.addWidget(self.mark_symbol, 1, 1)

        self.mark_list = QListWidget()
        mark_layout.addWidget(self.mark_list, 2, 0, 1, 2)

        btn_mark_remove = QPushButton("Remove")
        btn_mark_remove.setFixedWidth(70)
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
