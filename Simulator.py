
# This class runs the simulation loop, updates physics, and visualizes the results.

from Lander import Lander
from PhysicsEngine import PhysicsEngine
from DataLogger import DataLogger
import matplotlib.pyplot as plt

class Simulator:
    def __init__(self, planet):
        self.planet = planet
        self.lander = Lander(mass=1000, fuel_mass=500, thrust_power=15000, drag_coefficient=0.5, planet=planet)
        self.physics = PhysicsEngine(self.lander)
        self.logger = DataLogger()

    def run(self, thrust_angle=0.0, thrust_force=0.0, duration=60, dt=0.1):
        time = 0.0

        while time < duration and self.lander.position[1] > 0:
            self.physics.update(thrust_angle, thrust_force, dt)
            self.logger.log(time, self.lander.position[1], self.lander.velocity[1])
            print(f"Time: {time:.1f}s | Height: {self.lander.position[1]:.2f} m | Vy: {self.lander.velocity[1]:.2f} m/s")

            time += dt

        self.logger.plot()