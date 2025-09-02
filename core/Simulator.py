import numpy as np
from core.Lander import MoonLander
from core.PhysicsEngine import PhysicsEngine
from core.DataLogger import DataLogger
import matplotlib.pyplot as plt

class Simulator:
    def __init__(self, planet, controller=None, initial_altitude=1000.0):
        self.planet = planet
        self.lander = MoonLander(planet)
        self.lander.position = np.array([0.0, initial_altitude, 0.0])
        self.physics = PhysicsEngine(self.lander)
        self.logger = DataLogger()
        self.controller = controller

    def step(self, dt, thrust_vector=np.array([0.0, 1.0, 0.0]), thrust_force=None):
        # If controller is set, override thrust force
        if self.controller:
            vertical_velocity = self.lander.velocity[1]
            thrust_force = self.controller.update(vertical_velocity, dt)
        if thrust_force is None:
            thrust_force = 0.0

        self.physics.update(thrust_vector, thrust_force, dt)
        self.logger.log(None, self.lander.position, self.lander.velocity)  # time can be handled externally

    def get_telemetry(self):
        return {
            'position': self.lander.position.copy(),
            'velocity': self.lander.velocity.copy(),
            'orientation': self.lander.orientation.copy()
        }

    def reset(self, initial_altitude=1000.0):
        self.lander.position = np.array([0.0, initial_altitude, 0.0])
        self.lander.velocity = np.array([0.0, 0.0, 0.0])
        self.lander.orientation = np.array([0.0, 0.0, 0.0])
        self.lander.angular_velocity = np.array([0.0, 0.0, 0.0])
        self.logger = DataLogger()

    def run(self, thrust_vector=np.array([0.0, 1.0, 0.0]), thrust_force=300, duration=60, dt=0.1):
        time = 0.0
        while time < duration and self.lander.position[1] > 0:
            if self.controller:
                vertical_velocity = self.lander.velocity[1]
                thrust_force = self.controller.update(vertical_velocity, dt)
            self.physics.update(thrust_vector, thrust_force, dt)
            self.logger.log(time, self.lander.position, self.lander.velocity)
            print(f"Time: {time:.1f}s | Pos: {self.lander.position} | Vel: {self.lander.velocity} | Ori: {self.lander.orientation}")
            print(f"PID output (thrust): {thrust_force:.2f} N")
            time += dt
        self.logger.plot()

    def get_logger(self):
        return self.logger