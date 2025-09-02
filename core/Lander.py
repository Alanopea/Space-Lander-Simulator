
import numpy as np
from abc import ABC, abstractmethod

class Lander(ABC):
    def __init__(self, mass, fuel_mass, thrust_power, drag_coefficient, planet, dimensions):
        self.mass = mass
        self.fuel_mass = fuel_mass
        self.thrust_power = thrust_power
        self.drag_coefficient = drag_coefficient
        self.planet = planet
        self.dimensions = np.array(dimensions) # width, height, depth

        self.position = np.array([0.0, 1000.0, 0.0])
        self.velocity = np.array([0.0, 0.0, 0.0])
        self.orientation = np.array([0.0, 0.0, 0.0])
        self.angular_velocity = np.array([0.0, 0.0, 0.0])

        w, h, d = dimensions
        self.inertia = (1/12) * self.mass * np.array([
            h**2 + d**2,
            w**2 + d**2,
            w**2 + h**2,
        ])

    @abstractmethod
    def get_name(self):
        pass

class MoonLander(Lander):
    def __init__(self, planet):
        super().__init__(
            mass=15103, fuel_mass=8200, thrust_power=45000, drag_coefficient=0.8, planet=planet,
            dimensions=(8.2, 4.2, 6.4) # example dimensions
        )
    def get_name(self):
        return "Moon Lander"