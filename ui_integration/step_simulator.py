import numpy as np
from ui_integration.interfaces import ISimulator
from Lander import Lander
from PhysicsEngine import PhysicsEngine
from DataLogger import DataLogger

class StepSimulator(ISimulator):
    def __init__(self, planet, controller=None, initial_altitude=1000.0, lander_params=None):
        # Use default lander params if not provided
        lp = lander_params or dict(mass=1000, fuel_mass=500, thrust_power=15000, drag_coefficient=0.8, dimensions=(2.0,2.0,4.0))
        self.lander = Lander(
            mass=lp['mass'],
            fuel_mass=lp['fuel_mass'],
            thrust_power=lp['thrust_power'],
            drag_coefficient=lp['drag_coefficient'],
            planet=planet,
            dimensions=lp['dimensions']
        )
        # set initial altitude
        self.lander.position = np.array([0.0, initial_altitude, 0.0])
        self.physics = PhysicsEngine(self.lander)
        self.controller = controller
        self.logger = DataLogger()
        self.time = 0.0
        self.finished = False

    def reset(self):
        self.time = 0.0
        self.finished = False
        # reset lander state (could also re-instantiate for full reset)
        self.lander.position = np.array([0.0, self.lander.position[1], 0.0])
        self.lander.velocity = np.array([0.0, 0.0, 0.0])
        self.lander.orientation = np.array([0.0, 0.0, 0.0])
        self.lander.angular_velocity = np.array([0.0, 0.0, 0.0])
        self.logger = DataLogger()

    def step(self, dt):
        if self.finished:
            return self._telemetry()

        thrust_vector = np.array([0.0, 1.0, 0.0])
        thrust_force = 0.0

        # if controller present, compute thrust based on vertical velocity
        if self.controller is not None:
            vertical_velocity = self.lander.velocity[1]
            thrust_force = self.controller.update(vertical_velocity, dt)
            # clamp thrust between 0 and thrust_power (optional)
            thrust_force = max(0.0, min(thrust_force, self.lander.thrust_power))
        else:
            thrust_force = 0.0

        # call physics update (same signature as your PhysicsEngine.update)
        self.physics.update(thrust_vector, thrust_force, dt)

        # log
        self.logger.log(self.time, self.lander.position, self.lander.velocity)

        # time increment
        self.time += dt

        # check touchdown
        if self.lander.position[1] <= 0.0:
            self.finished = True

        return self._telemetry()

    def _telemetry(self):
        return {
            'time': self.time,
            'position': self.lander.position.copy(),
            'velocity': self.lander.velocity.copy(),
            'orientation': self.lander.orientation.copy(),
            'status': 'LANDED' if self.finished else 'DESCENDING'
        }

    def get_logger(self):
        return self.logger