from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QComboBox, QLabel, QDoubleSpinBox, QGroupBox
from PyQt5.QtCore import QTimer, Qt, QThread

from UI.panels.emergency_panel_UI import EmergencyPanel
from UI.panels.status_panel_UI import StatusPanel
from UI.panels.radar_panel_UI import RadarPanel
from core.EnvironmentManager import EnvironmentManager
from pid_controller import PIDController
from ui_integration.step_simulator import StepSimulator
from ui_integration.simulation_worker import SimulationWorker

import numpy as np


class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dashboard")
        self.setGeometry(100, 100, 1200, 700)

        # Panels
        self.status_panel = StatusPanel()
        self.emergency_panel = EmergencyPanel()
        self.radar_panel = RadarPanel(self)

        # Layouts
        top_layout = QHBoxLayout()
        top_layout.addStretch(1)
        top_layout.addWidget(self.status_panel)
        top_layout.addStretch(1)

        right_dock = QVBoxLayout()
        right_dock.addStretch(1)
        right_dock.addWidget(self.emergency_panel, 0, alignment=Qt.AlignRight)
        right_dock.setContentsMargins(0, 0, 35, 35)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.radar_panel, 3)
        bottom_layout.addLayout(right_dock, 0)

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addLayout(bottom_layout)

        self.setLayout(main_layout)

        # Simulation Controls
        self.env_manager = EnvironmentManager()
        control_box = QGroupBox("Simulation Controls")
        control_layout = QHBoxLayout()
        self.planet_selector = QComboBox()
        self.planet_selector.addItems(self.env_manager.list_planets())
        control_layout.addWidget(QLabel("Planet:"))
        control_layout.addWidget(self.planet_selector)
        control_layout.addWidget(QLabel("Kp"))
        self.kp_spin = QDoubleSpinBox(); self.kp_spin.setRange(0, 10000); self.kp_spin.setValue(300)
        control_layout.addWidget(self.kp_spin)
        control_layout.addWidget(QLabel("Ki"))
        self.ki_spin = QDoubleSpinBox(); self.ki_spin.setRange(0, 1000); self.ki_spin.setValue(0)
        control_layout.addWidget(self.ki_spin)
        control_layout.addWidget(QLabel("Kd"))
        self.kd_spin = QDoubleSpinBox(); self.kd_spin.setRange(0, 1000); self.kd_spin.setValue(120)
        control_layout.addWidget(self.kd_spin)
        self.start_btn = QPushButton("Start")
        self.pause_btn = QPushButton("Pause")
        self.stop_btn = QPushButton("Stop")
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.pause_btn)
        control_layout.addWidget(self.stop_btn)
        control_box.setLayout(control_layout)
        main_layout.insertWidget(1, control_box)

        self.sim_thread = None
        self.sim_worker = None

        self.start_btn.clicked.connect(self.start_simulation)
        self.pause_btn.clicked.connect(self.pause_simulation)
        self.stop_btn.clicked.connect(self.stop_simulation)

    # REMOVE update_dashboard and timer

    def start_simulation(self):
        planet_name = self.planet_selector.currentText()
        planet = self.env_manager.get_planet(planet_name)
        pid = PIDController(kp=self.kp_spin.value(), ki=self.ki_spin.value(), kd=self.kd_spin.value(), setpoint=-2.0)
        sim = StepSimulator(planet, controller=pid, initial_altitude=1000.0)

        self.sim_thread = QThread()
        self.sim_worker = SimulationWorker(sim, dt=0.1, duration=120.0)
        self.sim_worker.moveToThread(self.sim_thread)

        self.sim_thread.started.connect(self.sim_worker.run)
        self.sim_worker.telemetry.connect(self.on_telemetry)
        self.sim_worker.status_changed.connect(self.status_panel.set_status)
        self.sim_worker.alert.connect(self.on_alert)
        self.sim_worker.finished.connect(self.on_sim_finished)
        self.sim_worker.finished.connect(self.sim_thread.quit)
        self.sim_worker.finished.connect(self.sim_worker.deleteLater)
        self.sim_thread.finished.connect(self.sim_thread.deleteLater)

        self.sim_thread.start()

    def pause_simulation(self):
        if self.sim_worker:
            self.sim_worker.pause()

    def stop_simulation(self):
        if self.sim_worker:
            self.sim_worker.stop()

    def on_telemetry(self, t, pos, vel, ori):
        altitude = float(pos[1])
        yaw_deg = float(np.degrees(ori[2]))
        self.radar_panel.update_attitude(yaw=yaw_deg)
        status = "LANDED" if altitude <= 0 else "DESCENDING"
        self.status_panel.set_status(status)

    def on_alert(self, level, message):
        if level == "WARNING":
            self.emergency_panel.trigger_warning(message)
        elif level == "CAUTION":
            self.emergency_panel.trigger_caution(message)

    def on_sim_finished(self):
        if self.sim_worker:
            logger = self.sim_worker.sim.get_logger()
            logger.plot()
        self.sim_worker = None
        self.sim_thread = None


