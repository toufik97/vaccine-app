from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtCore import Qt, pyqtSignal

class DateLineEdit(QLineEdit):
    navigationRequested = pyqtSignal(int, int)

    def __init__(self, row, parent=None):
        super().__init__(parent)
        self.row = row

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Up:
            self.navigationRequested.emit(self.row, -1)
        elif event.key() == Qt.Key.Key_Down:
            self.navigationRequested.emit(self.row, 1)
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.navigationRequested.emit(self.row, 1)
        else:
            super().keyPressEvent(event)
