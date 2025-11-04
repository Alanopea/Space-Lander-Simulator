from PyQt5.QtWidgets import QWidget
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
from UI.panels.EnginePanelUI import EnginePanel
import numpy as np


class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Space Lander Simulator")
        self.setGeometry(100, 100, 1920, 1080)
        self.setStyleSheet("background-color: #E0E0E0;")

        # Panels
        self.status_panel = StatusPanel(self)
        self.emergency_panel = EmergencyPanel(self)
        self.radar_panel = RadarPanel(self)
        self.telemetry_panel = TelemetryPanel(self)
        self.engine_panel = EnginePanel(lander=None, parent=self)
        self.engine_panel.hide()
        self._controls = None  # SimulationPanel instance when connected

        # Simulation backend
        self.env_manager = EnvironmentManager()
        self.sim_thread = None
        self.sim_worker = None
        self.simulator_wrapper = None

    # ---------------- Layout Scaling ----------------
    def resizeEvent(self, event):
        w, h = self.width(), self.height()
        scale = min(w / 1920, h / 1080)

        # Status panel (centered top)
        sp_w, sp_h = int(450 * scale), int(60 * scale)
        sp_x = (w - sp_w) // 2
        sp_y = int(65 * scale)
        self.status_panel.setGeometry(sp_x, sp_y, sp_w, sp_h)

        # Telemetry panel (top-left)
        tp_w, tp_h = int(900 * scale), int(310 * scale)
        tp_x, tp_y = int(35 * scale), int(200 * scale)
        self.telemetry_panel.setGeometry(tp_x, tp_y, tp_w, tp_h)

        # Simulation panel (just above telemetry)
        if self._controls is not None:
            sim_h = int(100 * scale)
            sim_w = tp_w
            sim_x, sim_y = tp_x, tp_y - sim_h - int(10 * scale)
            self._controls.setGeometry(sim_x, sim_y, sim_w, sim_h)

        # Engine panel (top-right, fixed size)
        eng_w, eng_h = int(350 * scale), int(350 * scale)
        eng_x = w - eng_w - int(35 * scale)
        eng_y = int(35 * scale)
        self.engine_panel.setGeometry(eng_x, eng_y, eng_w, eng_h)

        # Radar panel (bottom-left)
        radar_w, radar_h = int(500 * scale), int(500 * scale)
        self.radar_panel.setGeometry(int(35 * scale), h - radar_h - int(35 * scale), radar_w, radar_h)

        # Emergency panel (bottom-right)
        ep_w, ep_h = int(400 * scale), int(300 * scale)
        self.emergency_panel.setGeometry(w - ep_w - int(35 * scale), h - ep_h - int(35 * scale), ep_w, ep_h)

        super().resizeEvent(event)


    # ---------------- Controls ----------------
    def connect_controls(self, controls: object):
        controls.setParent(self)
        self._controls = controls
        controls.startRequested.connect(self.start_simulation)
        controls.pauseToggled.connect(self._on_pause_toggled)
        controls.stopRequested.connect(self.stop_simulation)

    # ---------------- Simulation ----------------
    def start_simulation(self, planet_name: str = None):
        if self.sim_worker is not None:
            return

        planet = (
            self.env_manager.get_planet(planet_name)
            if planet_name
            else self.env_manager.get_planet(self.env_manager.list_planets()[0])
        )
        controller = make_default_controller()

        try:
            initial_altitude = float(getattr(self._controls, "initial_altitude", INITIAL_ALTITUDE))
        except Exception:
            initial_altitude = INITIAL_ALTITUDE

        try:
            initial_velocity = float(getattr(self._controls, "initial_velocity", INITIAL_VELOCITY))
        except Exception:
            initial_velocity = INITIAL_VELOCITY

        self.simulator_wrapper = StepSimulator(
            planet, controller=controller,
            initial_altitude=initial_altitude,
            initial_velocity=initial_velocity,
        )

        try:
            self.engine_panel.lander = self.simulator_wrapper.simulator.lander
            self.engine_panel.show()
            self.engine_panel.update_panel()
        except Exception:
            pass

        try:
            self.radar_panel.set_lander_dimensions(self.simulator_wrapper.simulator.lander.dimensions)
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
        try:
            if paused:
                self.sim_worker.pause()
            else:
                self.sim_worker.resume()
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
            if self.engine_panel is not None:
                self.engine_panel.lander = None
                self.engine_panel.hide()
        except Exception:
            pass
        self.sim_worker = None
        self.sim_thread = None
        self.simulator_wrapper = None
        try:
            if self._controls is not None:
                self._controls.reset_ui()
        except Exception:
            pass

    def on_telemetry(self, t, pos, vel, ori, **kwargs):
        try:
            yaw = float(np.degrees(ori[2])) if ori is not None else 0.0
        except Exception:
            yaw = 0.0
        self.radar_panel.update_attitude(yaw=yaw)
        self.status_panel.update_telemetry(t, pos, vel, ori)
        total_mass = kwargs.get("total_mass", None)
        fuel_mass = kwargs.get("fuel_mass", None)
        initial_fuel = kwargs.get("initial_fuel_mass", None)
        self.telemetry_panel.update_telemetry(
            t, pos, vel, ori,
            total_mass=total_mass, fuel_mass=fuel_mass,
            initial_fuel_mass=initial_fuel
        )
        try:
            if self.engine_panel and self.engine_panel.isVisible():
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
        try:
            if self.engine_panel is not None:
                self.engine_panel.lander = None
                self.engine_panel.hide()
        except Exception:
            pass
        self.sim_worker = None
        self.sim_thread = None
        self.simulator_wrapper = None
        try:
            if self._controls is not None:
                self._controls.reset_ui()
        except Exception:
            pass
