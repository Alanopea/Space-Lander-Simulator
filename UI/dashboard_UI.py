from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import Qt, QThread

from UI.panels.emergency_panel_UI import EmergencyPanel
from UI.panels.status_panel_UI import StatusPanel
from UI.panels.radar_panel_UI import RadarPanel
from core.EnvironmentManager import EnvironmentManager
from core.config import make_default_controller, INITIAL_ALTITUDE, INITIAL_VELOCITY
from ui_integration.step_simulator import StepSimulator
from ui_integration.simulation_worker import SimulationWorker
from UI.panels.telemetry_panel_UI import TelemetryPanel
from UI.panels.simulation_panel_UI import SimulationPanel

# Engine panel import
from UI.panels.EnginePanelUI import EnginePanel
from UI.panels.lander_3d_panel_UI import Lander3DPanel

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
        self.telemetry_panel = TelemetryPanel(self)
        self.lander_3d_panel = Lander3DPanel(self)

        # Layouts
        # store top_layout so controls can be inserted into it later
        self.top_layout = QHBoxLayout()
        self.top_layout.addStretch(1)
        self.top_layout.addWidget(self.status_panel)
        self.top_layout.addStretch(1)

        right_dock = QVBoxLayout()
        right_dock.addStretch(1)
        right_dock.addWidget(self.emergency_panel, 0, alignment=Qt.AlignRight)
        right_dock.setContentsMargins(0, 0, 35, 35)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.radar_panel, 2)
        bottom_layout.addWidget(self.lander_3d_panel, 3)
        bottom_layout.addLayout(right_dock, 0)

        self.main_layout = QVBoxLayout()
        self.main_layout.addLayout(self.top_layout)
        self.main_layout.addLayout(bottom_layout)

        self.setLayout(self.main_layout)

        # Simulation / env
        self.env_manager = EnvironmentManager()
        self.sim_thread = None
        self.sim_worker = None
        self.simulator_wrapper = None  # StepSimulator instance
        self._controls = None  # will hold SimulationPanel instance when connected
        self._last_time = None
        self._last_velocity = None

        # Engine panel (top-right). Create once and hide until simulation provides a lander
        self.engine_panel = EnginePanel(lander=None, parent=self)
        self.engine_panel.hide()

    def resizeEvent(self, event):
        # keep floating/overlay panels anchored when window resizes
        try:
            if self.engine_panel and self.engine_panel.isVisible():
                x = max(10, self.width() - self.engine_panel.width() - 20)
                y = 20
                self.engine_panel.move(x, y)
        except Exception:
            pass
        super().resizeEvent(event)

    # Public connector: attach controls signals to dashboard handlers
    def connect_controls(self, controls: object):
        """
        controls: instance of SimulationPanel
        This method will embed the controls widget into the dashboard UI and connect signals.
        """
        # parent it to the dashboard so it's visually contained
        controls.setParent(self)
        # insert controls at the left side of top_layout
        # insert at index 0 so it appears left-most
        self.top_layout.insertWidget(0, controls)
        self._controls = controls

        # connect signals
        controls.startRequested.connect(self.start_simulation)
        controls.pauseToggled.connect(self._on_pause_toggled)
        controls.stopRequested.connect(self.stop_simulation)

    def start_simulation(self, planet_name: str = None):
        # If a simulation is already running, ignore start
        if self.sim_worker is not None:
            return

        planet = self.env_manager.get_planet(planet_name) if planet_name else self.env_manager.get_planet(self.env_manager.list_planets()[0])

        # create controller from centralized config (default = LQR)
        controller = make_default_controller()

        # get initial altitude from controls (SimulationPanel) if available, else default from config
        try:
            initial_altitude = float(getattr(self._controls, "initial_altitude", INITIAL_ALTITUDE))
        except Exception:
            initial_altitude = INITIAL_ALTITUDE

        # get initial vertical velocity from controls if available, else default from config
        try:
            initial_velocity = float(getattr(self._controls, "initial_velocity", INITIAL_VELOCITY))
        except Exception:
            initial_velocity = INITIAL_VELOCITY

        # create fresh simulator wrapper each start
        self.simulator_wrapper = StepSimulator(planet, controller=controller, initial_altitude=initial_altitude, initial_velocity=initial_velocity)

        # attach engine panel to the current lander and place at top-right
        try:
            self.engine_panel.lander = self.simulator_wrapper.simulator.lander
            x = max(10, self.width() - self.engine_panel.width() - 20)
            y = 20
            self.engine_panel.move(x, y)
            self.engine_panel.show()
            self.engine_panel.update_panel()
        except Exception:
            pass

        # set radar and 3D lander dimensions if available
        try:
            lander = self.simulator_wrapper.simulator.lander
            self.radar_panel.set_lander_dimensions(lander.dimensions)
            # Configure 3D panel geometry and engine layout
            self.lander_3d_panel.set_lander_dimensions(lander.dimensions)
            engine_positions = [e.position for e in getattr(lander, "engines", [])]
            if engine_positions:
                self.lander_3d_panel.set_engine_layout(engine_positions)
        except Exception:
            pass

        self.sim_thread = QThread()
        self.sim_worker = SimulationWorker(self.simulator_wrapper, dt=0.1, duration=120.0)
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

    def _on_pause_toggled(self, paused: bool):
        if not self.sim_worker:
            return
        if paused:
            try:
                self.sim_worker.pause()
            except Exception:
                pass
        else:
            try:
                self.sim_worker.resume()
            except Exception:
                pass

    def stop_simulation(self):
        # Stop and reset state so Start can be used again without restarting app
        if self.sim_worker:
            try:
                self.sim_worker.stop()
            except Exception:
                pass

        # attempt graceful thread shutdown
        if self.sim_thread:
            try:
                self.sim_thread.quit()
                self.sim_thread.wait(2000)
            except Exception:
                pass

        # hide and detach engine panel
        try:
            if self.engine_panel is not None:
                self.engine_panel.lander = None
                self.engine_panel.hide()
        except Exception:
            pass

        # Ensure references removed
        self.sim_worker = None
        self.sim_thread = None
        self.simulator_wrapper = None

        # notify controls UI to reset buttons (if connected)
        try:
            if self._controls is not None:
                self._controls.reset_ui()
        except Exception:
            pass

    def on_telemetry(self, t, pos, vel, ori, extras):
        # radar expects yaw in degrees inside its update method
        try:
            yaw = float(np.degrees(ori[2])) if ori is not None else 0.0
        except Exception:
            yaw = 0.0
        self.radar_panel.update_attitude(yaw=yaw)
        self.status_panel.update_telemetry(t, pos, vel, ori)
        
        # Extract fuel/mass data from extras
        extras_dict = extras if isinstance(extras, dict) else {}
        total_mass = extras_dict.get("total_mass", None)
        fuel_mass = extras_dict.get("fuel_mass", None)
        initial_fuel = extras_dict.get("max_fuel_mass", None)
        fuel_consumption_rate = extras_dict.get("fuel_consumption_rate", None)
        dry_mass = extras_dict.get("dry_mass", None)
        
        self.telemetry_panel.update_telemetry(
            t, pos, vel, ori, 
            total_mass=total_mass, 
            fuel_mass=fuel_mass, 
            initial_fuel_mass=initial_fuel,
            fuel_consumption_rate=fuel_consumption_rate,
            dry_mass=dry_mass
        )

        # ---------------- 3D LANDER VISUALIZATION ----------------

        # Altitude (lander will actually move toward ground in panel)
        try:
            altitude = float(pos[1]) if pos is not None else 0.0
        except Exception:
            altitude = 0.0

        # Always start with zeroed total forces
        forces = {
            "thrust": np.zeros(3, dtype=float),
            "gravity": np.zeros(3, dtype=float),
            "drag": np.zeros(3, dtype=float),
        }
        # --- PANEL UPDATE ------------------------------------------
        try:
            if self.lander_3d_panel is not None and self.lander_3d_panel.is_enabled():
                self.lander_3d_panel.update_scene(
                    altitude_m=altitude,
                    orientation_rad=ori,
                    forces=forces,
                )
        except Exception:
            pass


        # refresh engine panel visuals if visible
        try:
            if self.engine_panel is not None and self.engine_panel.isVisible():
                self.engine_panel.update_panel()
        except Exception:
            pass

    def on_alert(self, level, message):
        self.emergency_panel.handle_alert(level, message)

    def on_sim_finished(self):
        if self.sim_worker:
            try:
                logger = self.sim_worker.sim.get_logger()
                logger.plot()
            except Exception:
                pass

        # ensure engine panel detached
        try:
            if self.engine_panel is not None:
                self.engine_panel.lander = None
                self.engine_panel.hide()
        except Exception:
            pass

        self.sim_worker = None
        self.sim_thread = None
        self.simulator_wrapper = None

        # reset control UI so Start becomes available again
        try:
            if self._controls is not None:
                self._controls.reset_ui()
        except Exception:
            pass