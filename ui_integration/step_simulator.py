import numpy as np
from ui_integration.interfaces import ISimulator
from core.Simulator import Simulator

class StepSimulator(ISimulator):
    def __init__(self, planet, controller=None, initial_altitude=1000.0, lander_class=None, lander_instance=None):
        # Forward lander_class/lander_instance into core.Simulator so UI can choose lander
        self.simulator = Simulator(planet, controller=controller, initial_altitude=initial_altitude,
                                   lander_class=lander_class, lander_instance=lander_instance)
        self.time = 0.0
        self.finished = False

    def reset(self):
        self.time = 0.0
        self.finished = False
        self.simulator.reset(initial_altitude=self.simulator.lander.position[1])

    def step(self, dt):
        if self.finished:
            return self._telemetry()

        self.simulator.step(dt)
        self.time += dt

        altitude = self.simulator.lander.position[1]
        if altitude <= 0.0:
            self.finished = True

        return self._telemetry()

    def _telemetry(self):
        telemetry = self.simulator.get_telemetry()
        telemetry['time'] = self.time
        telemetry['status'] = 'LANDED' if self.finished else 'DESCENDING'
        return telemetry

    def get_logger(self):
        return self.simulator.get_logger()