# ui_integration/simulation_worker.py
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
import time

class SimulationWorker(QObject):
    telemetry = pyqtSignal(float, object, object, object, object)   # time, position, velocity, orientation, extras_dict
    status_changed = pyqtSignal(str)
    alert = pyqtSignal(str, str)   # level, message
    finished = pyqtSignal()

    def __init__(self, simulator, dt=0.1, duration=60.0, emergency_scenario_name=None):
        super().__init__()
        self.sim = simulator  # object implementing ISimulator
        self.dt = dt
        self.duration = duration
        self.emergency_scenario_name = emergency_scenario_name
        self._running = False
        self._paused = False
        self._emergency_warned = False
        self._ascending_warned = False
        self._landing_warned = False

    @pyqtSlot()
    def run(self):
        """Long-running entry point. This will be executed in worker thread."""
        self.sim.reset()
        self._running = True
        elapsed = 0.0
        self.status_changed.emit("RUNNING")
        
        # Emit emergency scenario warning at start
        if self.emergency_scenario_name and self.emergency_scenario_name != "None":
            self._emit_emergency_warning()

        while self._running and elapsed < self.duration:
            # pause handling
            while self._paused and self._running:
                QThread.msleep(50)

            tel = self.sim.step(self.dt)
            pos = tel['position']
            vel = tel['velocity']
            ori = tel['orientation']
            t = tel['time']
            extras = tel.get('extras', {})

            # emit telemetry to UI
            self.telemetry.emit(t, pos, vel, ori, extras)

            # Alert logic
            altitude = float(pos[1])
            vertical_velocity = float(vel[1])
            
            # Low altitude caution
            if 0 < altitude < 100:
                self.alert.emit("CAUTION", "Low altitude margin! Prepare for throttle-up.")
            
            # Ascending warning
            if altitude > 0 and vertical_velocity > 0 and not self._ascending_warned:
                self.alert.emit("WARNING", "Craft is ascending during descent phase!")
                self._ascending_warned = True
            
            # Landing too fast warning
            if altitude <= 0 and vertical_velocity < -5.0 and not self._landing_warned:
                self.alert.emit("WARNING", f"CRASH DETECTED! Landing speed {abs(vertical_velocity):.1f} m/s > 5 m/s limit.")
                self._landing_warned = True
            
            # Reset ascending warning if landed
            if altitude <= 0:
                self._ascending_warned = False

            # stop if simulator says finished
            if tel['status'] == 'LANDED':
                break

            elapsed += self.dt
            # sleep to pace simulation (ms)
            QThread.msleep(int(self.dt * 1000))

    def _emit_emergency_warning(self):
        """Emit warning based on emergency scenario type."""
        scenario_map = {
            "One Engine Failure": "WARNING - One engine has failed! Adjust thrust allocation.",
            "Two Engine Failure": "WARNING - Two engines have failed! Prepare for emergency landing.",
            "One Engine Stuck at 100%": "WARNING - One engine stuck at maximum thrust! Manual control required.",
            "Response Lag: Mild (0.2s)": "CAUTION - Mild response lag (0.2s) enabled.",
            "Response Lag: Medium (0.5s)": "WARNING - Medium response lag (0.5s) enabled. Landing will be challenging.",
            "Response Lag: Severe (1.0s)": "WARNING - Severe response lag (1.0s) enabled! Start descent procedures early.",
        }
        
        message = scenario_map.get(self.emergency_scenario_name)
        if message:
            level, msg = message.split(" - ", 1) if " - " in message else ("WARNING", message)
            self.alert.emit(level, msg)

    @pyqtSlot()
    def stop(self):
        self._running = False

    @pyqtSlot()
    def pause(self):
        self._paused = True

    @pyqtSlot()
    def resume(self):
        self._paused = False
