from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QFrame
from PyQt5.QtCore import Qt, QTimer
import itertools
import os

LOG_PATH = os.path.join(os.path.dirname(__file__), "messages", "emergency_messages.txt")

# ---------- Log ----------
class EmergencyLog(QTextEdit):
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
        self._message_count = {}

    def load_from_file(self, path: str):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                self.setText(f.read())
        else:
            self.setText("[INFO] No emergency log file found.")

    def log(self, line: str):
        count = self._message_count.get(line, 0)
        if count >= 2:   # only log twice
            return
        self._message_count[line] = count + 1

        if not self.toPlainText().endswith("\n\n"):
            self.append("\n")
        self.append(line + "\n")


# ---------- Flashing Button ----------
class EmergencyButton(QPushButton):
    def __init__(self, label: str, color: str):
        super().__init__(label)
        self.color = color
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._toggle)
        self._cycle = itertools.cycle([True, False])
        self.setFixedSize(150, 42)

        self._base_css = (
            "background-color: #000; font-weight: 700; border-radius: 6px; "
            "padding: 6px 10px; "
        )
        self._apply(active=False)

    def _apply(self, active: bool):
        border_col = self.color if active else "#555"
        text_col = self.color if active else "#FFF"
        self.setStyleSheet(
            self._base_css +
            f"border: 2px solid {border_col}; color: {text_col};"
        )

    def _toggle(self):
        self._apply(active=next(self._cycle))

    def start_flashing(self, interval_ms: int = 400):
        if not self.timer.isActive():
            self.timer.start(interval_ms)

    def stop_flashing(self):
        self.timer.stop()
        self._apply(active=False)


# ---------- Panel ----------
class EmergencyPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setAlignment(Qt.AlignRight | Qt.AlignBottom)

        # Buttons
        self.btn_warning = EmergencyButton("WARNING", "#FF1744")
        self.btn_caution = EmergencyButton("CAUTION", "#FFD600")

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        buttons.addWidget(self.btn_warning)
        buttons.addWidget(self.btn_caution)

        # Log
        self.log = EmergencyLog(LOG_PATH)

        root.addLayout(buttons)
        root.addWidget(self.log)

    # ---- Public API ----
    def trigger_warning(self, message: str):
        self.btn_warning.start_flashing()
        self.log.log(f"[WARNING] {message}")

    def trigger_caution(self, message: str):
        self.btn_caution.start_flashing()
        self.log.log(f"[CAUTION] {message}")

    def clear_alerts(self):
        self.btn_warning.stop_flashing()
        self.btn_caution.stop_flashing()

    def handle_alert(self, level, message):
        if level == "WARNING":
            self.trigger_warning(message)
        elif level == "CAUTION":
            self.trigger_caution(message)

    def reset_alerts(self):
        """Reset all alerts and clear flashing state."""
        self.clear_alerts()
        self.log.setText("[SYSTEM] Emergency Log Initialized\n")
