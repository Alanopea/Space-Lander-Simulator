
# This class calculates forces and updates the lander's position and velocity based on physics.

import math
from Lander import Lander

class PhysicsEngine:
    def __init__(self, lander):
        self.lander = lander

    def update(self, thrust_angle, thrust_force, dt):
        g = self.lander.planet.gravity
        rho = self.lander.planet.air_density

        # Forces
        thrust_x = thrust_force * math.cos(thrust_angle)
        thrust_y = thrust_force * math.sin(thrust_angle)
        weight = self.lander.mass * g
        drag_x = -0.5 * rho * self.lander.velocity[0] ** 2 * self.lander.drag_coefficient
        drag_y = -0.5 * rho * self.lander.velocity[1] ** 2 * self.lander.drag_coefficient

        # Accelerations
        ax = (thrust_x + drag_x) / self.lander.mass
        ay = (thrust_y + drag_y - weight) / self.lander.mass

        # Update state
        self.lander.velocity[0] += ax * dt
        self.lander.velocity[1] += ay * dt
        self.lander.position[0] += self.lander.velocity[0] * dt
        self.lander.position[1] += self.lander.velocity[1] * dt
