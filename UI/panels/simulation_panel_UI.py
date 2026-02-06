from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QComboBox, QLabel, QPushButton, QGroupBox
from PyQt5.QtCore import pyqtSignal, Qt
from core.LanderManager import LanderManager

class SimulationPanel(QWidget):
    # Signals:
    # startRequested: emits dict with 'planet', 'lander', 'controller' keys
    startRequested = pyqtSignal(dict)
    # pauseToggled: emits True if pause requested, False if resume requested
    pauseToggled = pyqtSignal(bool)
    # stopRequested: emits when stop/reset requested
    stopRequested = pyqtSignal()

    def __init__(self, env_manager, parent=None):
        super().__init__(parent)
        self.env_manager = env_manager
        self.lander_manager = LanderManager()

        self.setWindowFlags(Qt.Widget)  # can be embedded or shown separately
        
        # Main vertical layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(8)

        # Configuration row
        config_layout = QHBoxLayout()
        config_layout.setSpacing(8)

        # Planet selector
        config_layout.addWidget(QLabel("Planet:"))
        self.planet_selector = QComboBox()
        self.planet_selector.addItems(self.env_manager.list_planets())
        config_layout.addWidget(self.planet_selector)

        # Lander selector
        config_layout.addWidget(QLabel("Lander:"))
        self.lander_selector = QComboBox()
        self._update_lander_options()
        config_layout.addWidget(self.lander_selector)

        # Controller selector
        config_layout.addWidget(QLabel("Controller:"))
        self.controller_selector = QComboBox()
        self.controller_selector.addItems(["PID", "LQR", "MPC"])
        config_layout.addWidget(self.controller_selector)

        main_layout.addLayout(config_layout)

        # Control buttons row
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        self.start_btn = QPushButton("Start")
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setEnabled(False)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)

        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.pause_btn)
        button_layout.addWidget(self.stop_btn)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        # State
        self._running = False
        self._paused = False

        # Connections
        self.planet_selector.currentTextChanged.connect(self._on_planet_changed)
        self.start_btn.clicked.connect(self._on_start)
        self.pause_btn.clicked.connect(self._on_pause_toggle)
        self.stop_btn.clicked.connect(self._on_stop)

    def _update_lander_options(self):
        """Update lander selector - show all landers with notes about compatibility."""
        planet_name = self.planet_selector.currentText()
        all_landers = self.lander_manager.list_landers()
        
        self.lander_selector.clear()
        for lander_name in all_landers:
            # Add note for Moon Lander that it's Moon-only
            if lander_name == "Moon Lander":
                display_name = f"{lander_name} (Moon only)"
            else:
                display_name = lander_name
            
            self.lander_selector.addItem(display_name, lander_name)  # Store original name as data

    def _on_planet_changed(self):
        """Handle planet selection change - refresh lander list (shows all landers)."""
        if not self._running:
            self._update_lander_options()

    def _on_start(self):
        if self._running:
            return
        planet_name = self.planet_selector.currentText()
        # Get the actual lander name from combo box data (removes "(Moon only)" suffix)
        lander_index = self.lander_selector.currentIndex()
        lander_name = self.lander_selector.itemData(lander_index) if lander_index >= 0 else self.lander_selector.currentText()
        # Fallback to current text if no data stored
        if not lander_name:
            lander_name = self.lander_selector.currentText().replace(" (Moon only)", "")
        controller_kind = self.controller_selector.currentText().lower()
        
        self._running = True
        self._paused = False
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.pause_btn.setText("Pause")
        
        # Emit configuration dict
        config = {
            'planet': planet_name,
            'lander': lander_name,
            'controller': controller_kind
        }
        self.startRequested.emit(config)

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