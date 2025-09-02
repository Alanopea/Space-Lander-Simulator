# ui_integration/simulation_worker.py
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
import time

class SimulationWorker(QObject):
    telemetry = pyqtSignal(float, object, object, object)   # time, position, velocity, orientation
    status_changed = pyqtSignal(str)
    alert = pyqtSignal(str, str)   # level, message
    finished = pyqtSignal()

    def __init__(self, simulator, dt=0.1, duration=60.0):
        super().__init__()
        self.sim = simulator  # object implementing ISimulator
        self.dt = dt
        self.duration = duration
        self._running = False
        self._paused = False

    @pyqtSlot()
    def run(self):
        """Long-running entry point. This will be executed in worker thread."""
        self.sim.reset()
        self._running = True
        elapsed = 0.0
        self.status_changed.emit("RUNNING")

        while self._running and elapsed < self.duration:
            # pause handling
            while self._paused and self._running:
                QThread.msleep(50)

            tel = self.sim.step(self.dt)
            pos = tel['position']
            vel = tel['velocity']
            ori = tel['orientation']
            t = tel['time']

            # emit telemetry to UI
            self.telemetry.emit(t, pos, vel, ori)

            # simple alert logic (adapt to your needs)
            if 0 < pos[1] < 100:
                self.alert.emit("CAUTION", "Low altitude margin! Prepare for throttle-up.")
            if tel['status'] == 'LANDED' and abs(vel[1]) > 5.0:
                self.alert.emit("WARNING", f"Touchdown detected with high descent rate ({vel[1]:.2f} m/s).")

            # stop if simulator says finished
            if tel['status'] == 'LANDED':
                break

            elapsed += self.dt
            # sleep to pace simulation (ms)
            QThread.msleep(int(self.dt * 1000))

        # finalize
        if tel['status'] == 'LANDED':
            self.status_changed.emit("LANDED")
        else:
            self.status_changed.emit("STOPPED")
        self.finished.emit()
        self._running = False

    @pyqtSlot()
    def stop(self):
        self._running = False

    @pyqtSlot()
    def pause(self):
        self._paused = True

    @pyqtSlot()
    def resume(self):
        self._paused = False
