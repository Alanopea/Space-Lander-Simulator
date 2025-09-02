from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import QTimer, Qt
from panels.emergency_panel_UI import EmergencyPanel
from panels.status_panel_UI import StatusPanel
from panels.radar_panel_UI import RadarPanel


class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dashboard")
        self.setGeometry(100, 100, 1200, 700)

        # ---- Panels ----
        self.status_panel = StatusPanel()
        self.emergency_panel = EmergencyPanel()
        self.radar_panel = RadarPanel(self)

        # ---- Layouts ----
        # Top bar (status panel centered)
        top_layout = QHBoxLayout()
        top_layout.addStretch(1)
        top_layout.addWidget(self.status_panel)
        top_layout.addStretch(1)

        # Left column (telemetry stacked)
        left_layout = QVBoxLayout()

        # Right dock (emergency panel bottom-right with margins)
        right_dock = QVBoxLayout()
        right_dock.addStretch(1)
        right_dock.addWidget(self.emergency_panel, 0, alignment=Qt.AlignRight)
        right_dock.setContentsMargins(0, 0, 35, 35)

        # Bottom layout (radar panel on left, telemetry in center, emergency on right)
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.radar_panel, 3)
        bottom_layout.addLayout(left_layout, 2)
        bottom_layout.addLayout(right_dock, 0)

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
        self.time += 0.2
        altitude = max(0, 200 - 10 * self.time)
        velocity = -10
        attitude = (0, 0, 0)

        status = "LANDED" if altitude <= 0 else "DESCENDING"

        # Update panels
        self.status_panel.set_status(status)
        self.radar_panel.update_attitude(yaw=self.time * 10)

        # ---- Alerts ----
        if 0 < altitude < 100:
            self.emergency_panel.trigger_caution("Low altitude margin! Prepare for throttle-up.")

        if altitude <= 0:
            self.emergency_panel.trigger_warning("Touchdown detected with high descent rate!")

