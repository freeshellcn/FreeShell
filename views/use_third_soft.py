
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QLabel)

from utils.icon_util import resource_path

EXAMPLE_DATA = [
    ("altgraph", "https://github.com/ronaldoussoren/altgraph"),
    ("bcrypt", "https://github.com/pyca/bcrypt"),
    ("cffi", "https://github.com/python-cffi/cffi"),
    ("cryptography", "https://github.com/pyca/cryptography/"),
    ("invoke", "https://github.com/pyinvoke/invoke"),
    ("packaging", "https://github.com/pypa/packaging"),
    ("paramiko", "https://github.com/paramiko/paramiko"),
    ("pefile", "https://github.com/erocarrera/pefile"),
    ("pycparser", "https://github.com/eliben/pycparser"),
    ("pyinstaller", "https://github.com/pyinstaller/pyinstaller"),
    ("pyinstaller-hooks-contrib", "https://github.com/pyinstaller/pyinstaller-hooks-contrib"),
    ("PyNaCl", "https://github.com/pyca/pynacl"),
    ("PySide6", "https://wiki.qt.io/Qt_for_Python"),
    ("PySide6_Addons", "https://wiki.qt.io/Qt_for_Python"),
    ("PySide6_Essentials", "https://wiki.qt.io/Qt_for_Python"),
    ("pywin32-ctypes", "https://github.com/enthought/pywin32-ctypes"),
    ("shiboken6", "https://wiki.qt.io/Qt_for_Python")
]

class UseThirdSoftDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.list_widget = None
        self.setWindowTitle("使用软件")
        self.setWindowIcon(QIcon(resource_path("resources/image/Logo.png")))
        self.setMinimumSize(400, 300)
        layout = QVBoxLayout(self)
        table = QTableWidget(self)
        table.setColumnCount(1)
        table.setHorizontalHeaderLabels(["软件"])
        table.setRowCount(len(EXAMPLE_DATA))
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # 禁止编辑
        table.verticalHeader().setVisible(False)

        # 填充数据：用 QLabel 显示 HTML 链接，并允许在外部浏览器打开
        for row, (name, name_url) in enumerate(EXAMPLE_DATA):
            name_label = QLabel()
            name_label.setTextFormat(Qt.TextFormat.RichText)
            name_label.setText(f'<a href="{name_url}">{name}</a>')
            name_label.setOpenExternalLinks(True)  # 点击在外部浏览器打开
            name_label.setToolTip(name_url)
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setCellWidget(row, 0, name_label)

        # 视觉调整（列宽自适应）
        table.resizeColumnsToContents()
        table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(table)
        self.setLayout(layout)
