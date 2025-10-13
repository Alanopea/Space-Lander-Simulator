from PyQt5.QtWidgets import QWidget, QHBoxLayout, QComboBox, QLabel, QPushButton, QGroupBox
from PyQt5.QtCore import pyqtSignal, Qt

class SimulationPanel(QWidget):
    # Signals:
    # startRequested: emits planet name
    startRequested = pyqtSignal(str)
    # pauseToggled: emits True if pause requested, False if resume requested
    pauseToggled = pyqtSignal(bool)
    # stopRequested: emits when stop/reset requested
    stopRequested = pyqtSignal()

    def __init__(self, env_manager, parent=None):
        super().__init__(parent)
        self.env_manager = env_manager

        self.setWindowFlags(Qt.Widget)  # can be embedded or shown separately
        layout = QHBoxLayout()
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        self.planet_selector = QComboBox()
        self.planet_selector.addItems(self.env_manager.list_planets())

        layout.addWidget(QLabel("Planet:"))
        layout.addWidget(self.planet_selector)

        self.start_btn = QPushButton("Start")
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setEnabled(False)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)

        layout.addWidget(self.start_btn)
        layout.addWidget(self.pause_btn)
        layout.addWidget(self.stop_btn)

        self.setLayout(layout)

        # State
        self._running = False
        self._paused = False

        # Connections
        self.start_btn.clicked.connect(self._on_start)
        self.pause_btn.clicked.connect(self._on_pause_toggle)
        self.stop_btn.clicked.connect(self._on_stop)

    def _on_start(self):
        if self._running:
            return
        planet_name = self.planet_selector.currentText()
        self._running = True
        self._paused = False
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.pause_btn.setText("Pause")
        self.startRequested.emit(planet_name)

    def _on_pause_toggle(self):
        if not self._running:
            return
        self._paused = not self._paused
        if self._paused:
            self.pause_btn.setText("Run")
        else:
            self.pause_btn.setText("Pause")
        self.pauseToggled.emit(self._paused)

    def _on_stop(self):
        if not self._running:
            return
        # reset control state
        self._running = False
        self._paused = False
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.pause_btn.setText("Pause")
        self.stopRequested.emit()

    # allow external reset (e.g. when sim finishes)
    def reset_ui(self):
        self._running = False
        self._paused = False
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.pause_btn.setText("Pause")