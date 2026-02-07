
# This class calculates linear and angular forces and updates the lander's state in 3D with aerodynamic drag.

import math
import numpy as np

class PhysicsEngine:
    def __init__(self, lander):
        self.lander = lander

    def _body_to_world_rotation_matrix(self):
        """
        Compute the rotation matrix from body frame to world frame using ZYX Euler angles.
        
        Euler angles (yaw, pitch, roll) stored in self.lander.orientation as:
        - orientation[0] = yaw (rotation about Z axis)
        - orientation[1] = pitch (rotation about Y axis)
        - orientation[2] = roll (rotation about X axis)
        
        Returns a 3x3 rotation matrix R_world_from_body such that:
        v_world = R @ v_body
        """
        yaw, pitch, roll = self.lander.orientation
        
        # Rotation matrices for ZYX convention
        # Rz(yaw)
        cos_yaw, sin_yaw = np.cos(yaw), np.sin(yaw)
        Rz = np.array([
            [cos_yaw, -sin_yaw, 0],
            [sin_yaw,  cos_yaw, 0],
            [0,        0,       1]
        ])
        
        # Ry(pitch)
        cos_pitch, sin_pitch = np.cos(pitch), np.sin(pitch)
        Ry = np.array([
            [cos_pitch,  0, sin_pitch],
            [0,          1, 0],
            [-sin_pitch, 0, cos_pitch]
        ])
        
        # Rx(roll)
        cos_roll, sin_roll = np.cos(roll), np.sin(roll)
        Rx = np.array([
            [1, 0,         0],
            [0, cos_roll, -sin_roll],
            [0, sin_roll,  cos_roll]
        ])
        
        # Combined rotation: R_world = Rz @ Ry @ Rx
        return Rz @ Ry @ Rx
    
    def update(self, thrust_vector, thrust_force, dt, wind_vector=np.array([0.0, 0.0, 0.0])):
        altitude = self.lander.position[1]
        g = self.lander.planet.gravity_at_height(altitude)  # Dynamic gravity
        rho = self.lander.planet.air_density
        mass = self.lander.mass

        # === LINEAR FORCES ===
        weight = np.array([0.0, -mass * g, 0.0])
        
        # Rotate thrust from body frame to world frame
        thrust_vector_normalized = np.asarray(thrust_vector, dtype=float)
        thrust_norm = np.linalg.norm(thrust_vector_normalized)
        if thrust_norm > 1e-12:
            thrust_vector_normalized = thrust_vector_normalized / thrust_norm
        
        # Apply rotation transformation
        R_body_to_world = self._body_to_world_rotation_matrix()
        thrust_vector_world = R_body_to_world @ thrust_vector_normalized
        
        thrust = thrust_vector_world * thrust_force

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