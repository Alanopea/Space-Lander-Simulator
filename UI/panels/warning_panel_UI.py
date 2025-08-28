from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QFrame

class WarningPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Warnings:"))

        self.warning_box = QTextEdit()
        self.warning_box.setReadOnly(True)
        self.warning_box.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.warning_box.setStyleSheet("color: red; font-weight: bold;")
        self.warning_box.setText("All systems nominal.")

        layout.addWidget(self.warning_box)
        self.setLayout(layout)

    def add_warning(self, message):
        self.warning_box.append(message)

    def set_status(self, message):
        self.warning_box.setText(message)