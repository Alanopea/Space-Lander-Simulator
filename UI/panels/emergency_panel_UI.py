from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QFrame
from PyQt5.QtCore import Qt, QTimer
import itertools
import os

LOG_PATH = os.path.join(os.path.dirname(__file__), "emergency_messages.txt")

# Log
class EmergencyLog(QTextEdit):
    """Black 'cmd' style log with spacing and no spam."""
    def __init__(self, log_file: str):
        super().__init__()
        self.setReadOnly(True)
        self.setFixedSize(500, 180)
        self.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.setStyleSheet("""
            background-color: #000;
            color: #00FF7F;
            font-family: Consolas, 'Courier New', monospace;
            font-size: 12px;
        """)
        self.load_from_file(log_file)

        # To prevent spamming
        self._message_count = {}

    def load_from_file(self, path: str):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                self.setText(f.read())
        else:
            self.setText("[INFO] No emergency log file found.")

    def log(self, line: str):
        # Show each unique message max 2 times
        count = self._message_count.get(line, 0)
        if count >= 2:
            return
        self._message_count[line] = count + 1

        # Add with two empty lines spacing
        if not self.toPlainText().endswith("\n\n"):
            self.append("\n")
        self.append(line + "\n")


# Button with flashing
class EmergencyButton(QPushButton):
    """
    Custom button that can flash border + text color.
    """
    def __init__(self, label: str, color: str, flash_mode: str = "border"):
        super().__init__(label)
        self.color = color
        self.flash_mode = flash_mode
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._toggle)
        self._cycle = itertools.cycle([True, False])
        self.setFixedSize(90, 42)

        self._base_css = (
            "background-color: #000; font-weight: 700; border-radius: 6px; "
            "padding: 6px 10px; "
        )
        self._apply(active=False)

    def _apply(self, active: bool):
        # Flash both border + text
        if active:
            border_col = self.color
            text_col = self.color
        else:
            border_col = "#555"
            text_col = "#FFF"
        self.setStyleSheet(
            self._base_css +
            f"border: 2px solid {border_col}; color: {text_col};"
        )


    def _toggle(self):
        self._apply(active=next(self._cycle))

    def flash(self, times: int = 3, interval_ms: int = 250):
        """Flash for a finite number of on/off cycles."""
        # times = number of 'on' states; need double for on/off
        self.start_flashing(interval_ms)
        QTimer.singleShot(interval_ms * times * 2, self.stop_flashing)

    def start_flashing(self, interval_ms: int = 250):
        self.timer.start(interval_ms)

    def stop_flashing(self):
        self.timer.stop()
        self._apply(active=False)

# ---------- Panel ----------
class EmergencyPanel(QWidget):
    """
    Top: TEST / WARNING / CAUTION buttons (ISS-inspired, frame flash).
    Bottom: cmd-like log area 500x180.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setAlignment(Qt.AlignRight | Qt.AlignBottom)

        # Buttons (TEST = background flash; WARNING/CAUTION = border flash)
        self.btn_test = EmergencyButton("TEST", "#00C853", flash_mode="background")
        self.btn_warning = EmergencyButton("WARNING", "#FF1744", flash_mode="border")
        self.btn_caution = EmergencyButton("CAUTION", "#FFD600", flash_mode="border")

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        buttons.addWidget(self.btn_test)
        buttons.addWidget(self.btn_warning)
        buttons.addWidget(self.btn_caution)

        # Log
        self.log = EmergencyLog(LOG_PATH)

        root.addLayout(buttons)
        root.addWidget(self.log)

        # Connections
        self.btn_test.clicked.connect(self._run_test)

    # ---- Public API for your simulation ----
    def trigger_warning(self, message: str):
        self.btn_warning.start_flashing()
        self.log.log(f"[WARNING] {message}")

    def trigger_caution(self, message: str):
        self.btn_caution.start_flashing()
        self.log.log(f"[CAUTION] {message}")

    def clear_alerts(self):
        self.btn_warning.stop_flashing()
        self.btn_caution.stop_flashing()

    # ---- Internals ----
    def _run_test(self):
        # TEST button itself flashes green; others flash their frame 3 times
        self.btn_test.flash(times=3, interval_ms=250)
        self.btn_warning.flash(times=3, interval_ms=250)
        self.btn_caution.flash(times=3, interval_ms=250)
