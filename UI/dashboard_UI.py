from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import QTimer
from panels.telemetry_panel_UI import TelemetryPanel
from panels.warning_panel_UI import WarningPanel
from panels.visualization_panel_UI import VisualizationPanel

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lunar Lander Simulation Dashboard")
        self.setGeometry(100, 100, 1200, 700)

        # Panels
        self.telemetry_panel = TelemetryPanel()
        self.warning_panel = WarningPanel()
        self.visualization_panel = VisualizationPanel()

        # Layout
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.telemetry_panel)
        left_layout.addWidget(self.warning_panel)

        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout, 2)
        main_layout.addWidget(self.visualization_panel, 3)

        self.setLayout(main_layout)

        # Timer for updates
        self.time = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_dashboard)
        self.timer.start(200)

    def update_dashboard(self):
        # Example fake data
        self.time += 0.2
        altitude = max(0, 1000 - 10 * self.time)
        velocity = -10
        attitude = (0, 0, 0)

        status = "LANDED" if altitude <= 0 else "Descending"
        self.telemetry_panel.update_telemetry(self.time, altitude, velocity, attitude, status)

        if altitude <= 0:
            self.warning_panel.set_status("Touchdown detected!")
