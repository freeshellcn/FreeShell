from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import QObject, Slot

class ClipboardBridge(QObject):
    @Slot(result=str)
    def read_text(self):
        return QGuiApplication.clipboard().text()

    @Slot(str)
    def write_text(self, text):
        QGuiApplication.clipboard().setText(text)