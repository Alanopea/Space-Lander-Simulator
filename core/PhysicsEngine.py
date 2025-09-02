
# This class calculates linear and angular forces and updates the lander's state in 3D with aerodynamic drag.

import math
import numpy as np

class PhysicsEngine:
    def __init__(self, lander):
        self.lander = lander

    
    def update(self, thrust_vector, thrust_force, dt, wind_vector=np.array([0.0, 0.0, 0.0])):
        altitude = self.lander.position[1]
        g = self.lander.planet.gravity_at_height(altitude)  # Dynamic gravity
        rho = self.lander.planet.air_density
        mass = self.lander.mass

        # === LINEAR FORCES ===
        weight = np.array([0.0, -mass * g, 0.0])
        thrust = thrust_vector * thrust_force

        relative_velocity = self.lander.velocity - wind_vector
        drag = -0.5 * rho * self.lander.drag_coefficient * np.square(relative_velocity) * np.sign(relative_velocity)

        # Total force
        net_force = thrust + drag + weight
        acceleration = net_force / mass

        # Update linear motion
        self.lander.velocity += acceleration * dt
        self.lander.position += self.lander.velocity * dt

        # === ROTATIONAL FORCES ===
        torque = np.cross(self.lander.dimensions / 2, drag)  # Simple drag-induced torque
        angular_acceleration = torque / self.lander.inertia
        self.lander.angular_velocity += angular_acceleration * dt
        self.lander.orientation += self.lander.angular_velocity * dt