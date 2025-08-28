from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

class StatusPanel(QWidget):
    STATUS_COLORS = {
        "LANDED": "green",
        "CRASHED": "red",
        "WARNING": "orange",
        "DESCENDING": "blue",
        "IDLE": "gray"
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(550, 70)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel("IDLE")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont("Courier", 28, QFont.Bold))  # retro style
        self.label.setStyleSheet("color: black;")  # text always black
        layout.addWidget(self.label)

        self.setLayout(layout)

        self.current_status = "IDLE"
        self.previous_status = "IDLE"

        # Flash timer for WARNING
        self.flash_timer = QTimer()
        self.flash_timer.timeout.connect(self._flash_background)
        self.flash_state = False

        # Auto-reset timer for WARNING
        self.reset_timer = QTimer()
        self.reset_timer.setSingleShot(True)
        self.reset_timer.timeout.connect(self._reset_status)

        self._update_ui("IDLE")

    def set_status(self, status):
        """Change the status and update UI"""
        if status == "WARNING":
            # Save previous state
            self.previous_status = self.current_status
            self._start_warning_mode()
        else:
            self.current_status = status
            self._update_ui(status)

    def _update_ui(self, status):
        color = self.STATUS_COLORS.get(status, "gray")
        self.label.setText(status)
        self.setStyleSheet(f"background-color: {color}; border: 2px solid black;")

    def _start_warning_mode(self):
        self.current_status = "WARNING"
        self._update_ui("WARNING")
        self.flash_state = False
        self.flash_timer.start(500)  # flash every 500 ms
        self.reset_timer.start(5000)  # auto reset after 5 seconds

    def _flash_background(self):
        """Toggle background flashing effect"""
        if self.flash_state:
            self.setStyleSheet("background-color: orange; border: 2px solid black;")
        else:
            self.setStyleSheet("background-color: black; border: 2px solid black; color: orange;")
        self.flash_state = not self.flash_state

    def _reset_status(self):
        """Return to previous status after WARNING"""
        self.flash_timer.stop()
        self.set_status(self.previous_status)