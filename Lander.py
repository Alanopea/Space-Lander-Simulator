
# This class holds the current state of the lander: mass, fuel, position, velocity orintation and angular velocity.

import numpy as np

class Lander:
    def __init__(self, mass, fuel_mass, thrust_power, drag_coefficient, planet, dimensions=(2.0, 2.0, 4.0)):
        self.mass = mass
        self.fuel_mass = fuel_mass
        self.thrust_power = thrust_power
        self.drag_coefficient = drag_coefficient
        self.planet = planet
        self.dimensions = np.array(dimensions) # width, height, depth

        # Linear motion in 3D
        self.position = np.array([0.0, 1000.0, 0.0]) # x, y, z
        self.velocity = np.array([0.0, 0.0, 0.0]) # vx, vy, vz

        #Angular motion
        self.orientation = np.array([0.0, 0.0, 0.0]) # Euler angles: roll, pitch, yaw
        self.angular_velocity = np.array([0.0, 0.0, 0.0]) # rad/s

        # Moment of inertia for a cuboid
        w, h, d = dimensions
        self.inertia = (1/12) * self.mass * np.array([
            h**2 + d**2, # I_x
            w**2 + d**2, # I_y
            w**2 + h**2, # I_z
        ])