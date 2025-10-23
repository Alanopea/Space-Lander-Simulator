import numpy as np
from ui_integration.interfaces import ISimulator
from core.Simulator import Simulator

class StepSimulator(ISimulator):
    def __init__(self, planet, controller=None, initial_altitude=1000.0, lander_class=None, lander_instance=None):
        """
        Adapter that exposes a simple step/reset/get_logger interface for the UI.
        Keeps its own initial_altitude so reset() returns to the same start state.
        """
        self.initial_altitude = float(initial_altitude)
        self.simulator = Simulator(
            planet,
            controller=controller,
            initial_altitude=self.initial_altitude,
            lander_class=lander_class,
            lander_instance=lander_instance
        )
        self.time = 0.0
        self.finished = False

    def reset(self):
        self.time = 0.0
        self.finished = False
        # Reset simulator to the configured initial altitude
        if hasattr(self.simulator, "reset"):
            self.simulator.reset(initial_altitude=self.initial_altitude)

    def step(self, dt):
        """
        Advance simulation by dt and return a telemetry dict:
        {
          'time': float,
          'position': np.array,
          'velocity': np.array,
          'orientation': np.array,
          'status': 'DESCENDING'|'LANDED',
          'extras': { ... }  # optional telemetry extras (mass, fuel, ...)
        }
        """
        if self.finished:
            return self._telemetry()

        # advance core simulator one step
        self.simulator.step(dt)
        self.time += float(dt)

        return self._telemetry()

    def _telemetry(self):
        core_tel = self.simulator.get_telemetry()
        pos = core_tel.get('position')
        vel = core_tel.get('velocity')
        ori = core_tel.get('orientation')

        status = 'LANDED' if (pos is not None and pos[1] <= 0.0) else 'DESCENDING'
        if status == 'LANDED':
            self.finished = True

        extras = {}
        lander = getattr(self.simulator, "lander", None)
        if lander is not None and hasattr(lander, "telemetry_extras"):
            try:
                extras = lander.telemetry_extras()
            except Exception:
                extras = {}

        return {
            'time': self.time,
            'position': pos,
            'velocity': vel,
            'orientation': ori,
            'status': status,
            'extras': extras
        }

    def get_logger(self):
        return self.simulator.get_logger()