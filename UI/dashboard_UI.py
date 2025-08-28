from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import QTimer
from panels.telemetry_panel_UI import TelemetryPanel
from panels.warning_panel_UI import WarningPanel
from panels.status_panel_UI import StatusPanel
from panels.radar_panel_UI import RadarPanel


class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lunar Lander Simulation Dashboard")
        self.setGeometry(100, 100, 1200, 700)

        # Panels
        self.status_panel = StatusPanel()
        self.telemetry_panel = TelemetryPanel()
        self.warning_panel = WarningPanel()
        self.radar_panel = RadarPanel(self)

        # ---- Layouts ----
        # Top bar (status panel centered)
        top_layout = QHBoxLayout()
        top_layout.addStretch(1)
        top_layout.addWidget(self.status_panel)
        top_layout.addStretch(1)

        # Left column (telemetry + warnings stacked)
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.telemetry_panel)
        left_layout.addWidget(self.warning_panel)

        # Bottom layout (radar panel on left, telemetry+warnings on right)
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.radar_panel, 3)
        bottom_layout.addLayout(left_layout, 2)

        # Main vertical layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)      # status at top
        main_layout.addLayout(bottom_layout)   # rest of UI below

        self.setLayout(main_layout)

        # ---- Timer for updates ----
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

        status = "LANDED" if altitude <= 0 else "DESCENDING"

        # Update panels
        self.telemetry_panel.update_telemetry(self.time, altitude, velocity, attitude, status)
        self.status_panel.set_status(status)
        self.radar_panel.update_attitude(yaw=self.time * 10)

        if altitude <= 0:
            self.warning_panel.set_status("Touchdown detected!")
