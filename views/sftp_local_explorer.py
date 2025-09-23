from PySide6.QtCore import (
    Qt
)
from PySide6.QtWidgets import (
    QFileSystemModel
)


class LocalFileSystemModel(QFileSystemModel):
    def __init__(self):
        super().__init__()

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            headers = ["名称", "大小", "类型", "修改时间"]
            if 0 <= section < len(headers):
                return headers[section]
        return super().headerData(section, orientation, role)
