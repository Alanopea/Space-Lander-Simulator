# This class provides reusable rigid body rotational dynamics for complex shapes.

import numpy as np

class RigidBody:
    def __init__(self, mass, dimensions):
        self.mass = mass
        self.dimensions = dimensions
        w, h, d = dimensions
        self.inertia = (1/12) * mass * np.array([h**2 + d**2, w**2 + d**2, w**2 + h**2])

    def apply_torque(self, torque, angular_velocity, dt):
        angular_acceleration = torque / self.inertia
        return angular_velocity + angular_acceleration * dt