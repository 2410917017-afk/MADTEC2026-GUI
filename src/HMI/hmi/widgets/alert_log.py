from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QTextEdit


class AlertLog(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumSize(300, 2000)
        self.setPlaceholderText("...")
        self.setFont(QFont("Arial", 12, QFont.Bold))
        self.setStyleSheet("color: #dddcde; background-color: #5e5e5e; border-radius: 10px; ")
        self.setReadOnly(True)

    def escribirAlerta(self, texto):
        texto_actual = self.toPlainText()
        self.setPlainText(">" + texto + "\n" + "\n" + texto_actual)
