from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QComboBox, QLabel, QPushButton, QGroupBox, QLineEdit
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QIntValidator, QColor
from core.LanderManager import LanderManager
from core.emergencies.EmergencyScenarioManager import EmergencyScenarioManager

class SimulationPanel(QWidget):
    # Signals:
    # startRequested: emits dict with 'planet', 'lander', 'controller', 'emergency_scenario' keys
    startRequested = pyqtSignal(dict)
    # pauseToggled: emits True if pause requested, False if resume requested
    pauseToggled = pyqtSignal(bool)
    # stopRequested: emits when stop/reset requested
    stopRequested = pyqtSignal()

    def __init__(self, env_manager, parent=None):
        super().__init__(parent)
        self.env_manager = env_manager
        self.lander_manager = LanderManager()
        self.emergency_scenario_manager = EmergencyScenarioManager()

        self.setWindowFlags(Qt.Widget)  # can be embedded or shown separately
        
        # Main vertical layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(8)

        # Configuration row 1
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

        # Configuration row 2 - Emergency scenarios
        emergency_layout = QHBoxLayout()
        emergency_layout.setSpacing(8)

        # Emergency scenario selector
        emergency_layout.addWidget(QLabel("Emergency Scenario:"))
        self.emergency_scenario_selector = QComboBox()
        self.emergency_scenario_selector.addItems(self.emergency_scenario_manager.list_scenarios())
        emergency_layout.addWidget(self.emergency_scenario_selector)

        # Add stretch to push emergency scenario to the left
        emergency_layout.addStretch()

        main_layout.addLayout(emergency_layout)

        # Configuration row 3 - Initial conditions
        initial_conditions_layout = QHBoxLayout()
        initial_conditions_layout.setSpacing(8)

        # Initial altitude input
        initial_conditions_layout.addWidget(QLabel("Initial Altitude (m):"))
        self.altitude_input = QLineEdit()
        self.altitude_input.setPlaceholderText("100-9999")
        self.altitude_input.setMaxLength(4)
        self.altitude_input.setText("500")
        initial_conditions_layout.addWidget(self.altitude_input, 1)

        # Initial velocity input
        initial_conditions_layout.addWidget(QLabel("Initial Velocity (m/s):"))
        self.velocity_input = QLineEdit()
        self.velocity_input.setPlaceholderText("0-999")
        self.velocity_input.setMaxLength(3)
        self.velocity_input.setText("70")
        initial_conditions_layout.addWidget(self.velocity_input, 1)

        main_layout.addLayout(initial_conditions_layout)

        # Error message label
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red; font-weight: bold;")
        self.error_label.setVisible(False)
        main_layout.addWidget(self.error_label)

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

    def _validate_initial_conditions(self):
        """
        Validate initial altitude and velocity inputs.
        Returns tuple: (is_valid, altitude, velocity)
        """
        self.error_label.setVisible(False)
        
        # Validate altitude
        altitude_text = self.altitude_input.text().strip()
        if not altitude_text:
            self.error_label.setText("Error: Initial Altitude cannot be empty")
            self.error_label.setVisible(True)
            return False, None, None
        
        try:
            altitude = float(altitude_text)
        except ValueError:
            self.error_label.setText("Error: Initial Altitude must be a number")
            self.error_label.setVisible(True)
            return False, None, None
        
        if altitude < 100:
            self.error_label.setText("Error: Minimum altitude is 100m")
            self.error_label.setVisible(True)
            return False, None, None
        
        if altitude > 9999:
            self.error_label.setText("Error: Maximum altitude is 9999m")
            self.error_label.setVisible(True)
            return False, None, None
        
        # Validate velocity
        velocity_text = self.velocity_input.text().strip()
        if not velocity_text:
            self.error_label.setText("Error: Initial Velocity cannot be empty")
            self.error_label.setVisible(True)
            return False, None, None
        
        try:
            velocity = float(velocity_text)
        except ValueError:
            self.error_label.setText("Error: Initial Velocity must be a number")
            self.error_label.setVisible(True)
            return False, None, None
        
        if velocity < 0:
            self.error_label.setText("Error: Initial Velocity must be positive (will be converted to negative)")
            self.error_label.setVisible(True)
            return False, None, None
        
        if velocity > 999:
            self.error_label.setText("Error: Maximum velocity is 999 m/s")
            self.error_label.setVisible(True)
            return False, None, None
        
        # Convert velocity to negative (for downward descent)
        velocity = -velocity
        
        return True, altitude, velocity

    def _on_start(self):
        if self._running:
            return
        
        # Validate initial conditions
        is_valid, altitude, velocity = self._validate_initial_conditions()
        if not is_valid:
            return
        
        planet_name = self.planet_selector.currentText()
        # Get the actual lander name from combo box data (removes "(Moon only)" suffix)
        lander_index = self.lander_selector.currentIndex()
        lander_name = self.lander_selector.itemData(lander_index) if lander_index >= 0 else self.lander_selector.currentText()
        # Fallback to current text if no data stored
        if not lander_name:
            lander_name = self.lander_selector.currentText().replace(" (Moon only)", "")
        controller_kind = self.controller_selector.currentText().lower()
        emergency_scenario_name = self.emergency_scenario_selector.currentText()
        
        self._running = True
        self._paused = False
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.pause_btn.setText("Pause")
        
        # Emit configuration dict with initial conditions
        config = {
            'planet': planet_name,
            'lander': lander_name,
            'controller': controller_kind,
            'emergency_scenario': emergency_scenario_name,
            'initial_altitude': altitude,
            'initial_velocity': velocity
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