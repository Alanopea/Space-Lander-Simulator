from PyQt5.QtWidgets import QWidget, QGridLayout
from PyQt5.QtCore import Qt, QThread

from UI.panels.emergency_panel_UI import EmergencyPanel
from UI.panels.status_panel_UI import StatusPanel
from UI.panels.radar_panel_UI import RadarPanel
from UI.panels.telemetry_panel_UI import TelemetryPanel
from UI.panels.simulation_panel_UI import SimulationPanel
from UI.panels.EnginePanelUI import EnginePanel
from UI.panels.lander_3d_panel_UI import Lander3DPanel

from core.EnvironmentManager import EnvironmentManager
from core.LanderManager import LanderManager
from core.emergencies.EmergencyScenarioManager import EmergencyScenarioManager
from core.config import make_controller_by_kind, get_initial_altitude, get_initial_velocity
from ui_integration.step_simulator import StepSimulator
from ui_integration.simulation_worker import SimulationWorker

import numpy as np


class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dashboard")

        # Full HD base size (design reference)
        self.resize(1920, 1080)

        # Panels
        self.status_panel = StatusPanel()
        self.emergency_panel = EmergencyPanel(self)
        self.radar_panel = RadarPanel(self)
        self.telemetry_panel = TelemetryPanel(self)
        self.lander_3d_panel = Lander3DPanel(self)

        self.engine_panel = EnginePanel(lander=None, parent=self)
        self.engine_panel.hide()

        # Controls placeholder
        self._controls = None

        # ---------- GRID LAYOUT ----------
        self.grid = QGridLayout()
        self.grid.setContentsMargins(20, 20, 20, 20)
        self.grid.setSpacing(10)

        # TOP ROW
        self.grid.addWidget(self.status_panel, 0, 1, alignment=Qt.AlignCenter)
        self.grid.addWidget(self.engine_panel, 2, 2, alignment=Qt.AlignRight)

        # MIDDLE ROW
        self.grid.addWidget(self.radar_panel, 1, 0, alignment=Qt.AlignLeft)
        self.grid.addWidget(self.lander_3d_panel, 1, 1, 2, 1)
        self.grid.addWidget(self.telemetry_panel, 1, 2, alignment=Qt.AlignRight)

        self.grid.addWidget(self.emergency_panel, 2, 0, alignment=Qt.AlignLeft)
        self.grid.addWidget(self.engine_panel, 2, 2, alignment=Qt.AlignRight)

        # STRETCH RATIOS (Full HD intent)
        self.grid.setRowStretch(0, 1)   # Top bar
        self.grid.setRowStretch(1, 7)   # Main area

        self.grid.setColumnStretch(0, 3)  # Radar
        self.grid.setColumnStretch(1, 5)  # 3D Lander
        self.grid.setColumnStretch(2, 2)  # Telemetry

        self.setLayout(self.grid)

        # Simulation / env
        self.env_manager = EnvironmentManager()
        self.lander_manager = LanderManager()
        self.emergency_scenario_manager = EmergencyScenarioManager()
        self.sim_thread = None
        self.sim_worker = None
        self.simulator_wrapper = None

        # Floating emergency panel
        #self.emergency_panel.raise_()

    # ---------- RESIZE EVENT ----------
    #def resizeEvent(self, event):
        # Bottom-right floating emergency panel
        #try:
        #    if self.emergency_panel:
        #        x = self.width() - self.emergency_panel.width() - 30
        #        y = self.height() - self.emergency_panel.height() - 30
        #        self.emergency_panel.move(x, y)
        #    except Exception:
        #        pass

        #super().resizeEvent(event)

    # ---------- CONNECT CONTROLS ----------
    def connect_controls(self, controls: SimulationPanel):
        controls.setParent(self)
        self._controls = controls

        # Insert controls top-left
        self.grid.addWidget(controls, 0, 0, alignment=Qt.AlignLeft)

        controls.startRequested.connect(self.start_simulation)
        controls.pauseToggled.connect(self._on_pause_toggled)
        controls.stopRequested.connect(self.stop_simulation)

    # ---------- SIMULATION ----------
    def start_simulation(self, config=None):
        """
        Start simulation with configuration.
        
        Args:
            config: Dict with 'planet', 'lander', 'controller' keys, or None for defaults
        """
        if self.sim_worker is not None:
            return

        # Handle both old (str) and new (dict) signal formats for backward compatibility
        if isinstance(config, str):
            # Legacy: planet_name as string
            planet_name = config
            lander_name = None
            controller_kind = None
            emergency_scenario_name = None
        elif isinstance(config, dict):
            planet_name = config.get('planet')
            lander_name = config.get('lander')
            controller_kind = config.get('controller')
            emergency_scenario_name = config.get('emergency_scenario')
        else:
            # Defaults
            planet_name = None
            lander_name = None
            controller_kind = None
            emergency_scenario_name = None

        # Get planet
        planet = (
            self.env_manager.get_planet(planet_name)
            if planet_name
            else self.env_manager.get_planet(self.env_manager.list_planets()[0])
        )

        # Get lander class
        lander_class = None
        if lander_name:
            lander_class = self.lander_manager.get_lander_class(lander_name)
        
        # Get controller
        controller = make_controller_by_kind(controller_kind)

        # Get emergency scenario config
        emergency_scenario_config = None
        if emergency_scenario_name and emergency_scenario_name != "None":
            emergency_scenario_config = self.emergency_scenario_manager.get_scenario_config(emergency_scenario_name)

        # Get planet-specific initial conditions (with fallback to defaults)
        initial_altitude = get_initial_altitude(planet)
        initial_velocity = get_initial_velocity(planet)
        
        # Allow UI controls to override planet defaults if present
        try:
            if hasattr(self._controls, "initial_altitude"):
                initial_altitude = float(self._controls.initial_altitude)
        except Exception:
            pass

        try:
            if hasattr(self._controls, "initial_velocity"):
                initial_velocity = float(self._controls.initial_velocity)
        except Exception:
            pass

        self.simulator_wrapper = StepSimulator(
            planet,
            controller=controller,
            initial_altitude=initial_altitude,
            initial_velocity=initial_velocity,
            lander_class=lander_class,
            emergency_scenario_config=emergency_scenario_config
        )

        # Engine panel attach
        try:
            self.engine_panel.lander = self.simulator_wrapper.simulator.lander
            self.engine_panel.show()
            self.engine_panel.update_panel()
        except Exception:
            pass

        # Configure radar / 3D
        try:
            lander = self.simulator_wrapper.simulator.lander
            self.radar_panel.set_lander_dimensions(lander.dimensions)
            self.lander_3d_panel.set_lander_dimensions(lander.dimensions)

            engine_positions = [e.position for e in getattr(lander, "engines", [])]
            if engine_positions:
                self.lander_3d_panel.set_engine_layout(engine_positions)
        except Exception:
            pass

        self.sim_thread = QThread()
        self.sim_worker = SimulationWorker(
            self.simulator_wrapper, 
            dt=0.1, 
            duration=3600.0,
            emergency_scenario_name=emergency_scenario_name
        )
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
        try:
            self.sim_worker.pause() if paused else self.sim_worker.resume()
        except Exception:
            pass

    def stop_simulation(self):
        if self.sim_worker:
            try:
                self.sim_worker.stop()
            except Exception:
                pass

        if self.sim_thread:
            try:
                self.sim_thread.quit()
                self.sim_thread.wait(2000)
            except Exception:
                pass

        try:
            self.engine_panel.lander = None
            self.engine_panel.hide()
        except Exception:
            pass

        try:
            self.emergency_panel.reset_alerts()
        except Exception:
            pass

        self.sim_worker = None
        self.sim_thread = None
        self.simulator_wrapper = None

        try:
            if self._controls:
                self._controls.reset_ui()
        except Exception:
            pass

    # ---------- TELEMETRY ----------
    def on_telemetry(self, t, pos, vel, ori, extras):
        try:
            yaw = float(np.degrees(ori[2])) if ori is not None else 0.0
        except Exception:
            yaw = 0.0

        self.radar_panel.update_attitude(yaw=yaw)
        self.status_panel.update_telemetry(t, pos, vel, ori)

        extras_dict = extras if isinstance(extras, dict) else {}

        self.telemetry_panel.update_telemetry(
            t, pos, vel, ori,
            total_mass=extras_dict.get("total_mass"),
            fuel_mass=extras_dict.get("fuel_mass"),
            initial_fuel_mass=extras_dict.get("max_fuel_mass"),
            fuel_consumption_rate=extras_dict.get("fuel_consumption_rate"),
            dry_mass=extras_dict.get("dry_mass"),
        )

        # 3D Panel
        try:
            altitude = float(pos[1]) if pos is not None else 0.0
        except Exception:
            altitude = 0.0

        forces = {
            "thrust": np.zeros(3),
            "gravity": np.zeros(3),
            "drag": np.zeros(3),
        }

        try:
            if self.lander_3d_panel.is_enabled():
                self.lander_3d_panel.update_scene(
                    altitude_m=altitude,
                    orientation_rad=ori,
                    forces=forces,
                )
        except Exception:
            pass

        try:
            if self.engine_panel.isVisible():
                self.engine_panel.update_panel()
        except Exception:
            pass

    def on_alert(self, level, message):
        self.emergency_panel.handle_alert(level, message)

    def on_sim_finished(self):
        try:
            self.engine_panel.lander = None
            self.engine_panel.hide()
        except Exception:
            pass

        self.sim_worker = None
        self.sim_thread = None
        self.simulator_wrapper = None

        try:
            if self._controls:
                self._controls.reset_ui()
        except Exception:
            pass
