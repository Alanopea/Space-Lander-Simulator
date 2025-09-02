import numpy as np
from Lander import Lander
from PhysicsEngine import PhysicsEngine
from DataLogger import DataLogger
import matplotlib.pyplot as plt

class Simulator:
    def __init__(self, planet, controller=None):
        self.planet = planet
        self.lander = Lander(
            mass=1000,
            fuel_mass=500,
            thrust_power=15000,
            drag_coefficient=0.8,
            planet=planet
        )
        self.physics = PhysicsEngine(self.lander)
        self.logger = DataLogger()
        self.controller = controller  # Accept any controller (Open/Closed loop)

    def run(self, thrust_vector=np.array([0.0, 1.0, 0.0]), thrust_force=300, duration=60, dt=0.1):
        time = 0.0

        while time < duration and self.lander.position[1] > 0:
            # If controller is set, override thrust force
            if self.controller:
                vertical_velocity = self.lander.velocity[1]
                thrust_force = self.controller.update(vertical_velocity, dt)

            self.physics.update(thrust_vector, thrust_force, dt)
            self.logger.log(time, self.lander.position, self.lander.velocity)

            print(f"Time: {time:.1f}s | Pos: {self.lander.position} | Vel: {self.lander.velocity} | Ori: {self.lander.orientation}")
            print(f"PID output (thrust): {thrust_force:.2f} N")
            time += dt

        self.logger.plot()