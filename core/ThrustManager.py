"""Thrust allocation and management."""

import numpy as np
from core.ThrustAllocator import ThrustAllocator

class ThrustManager:
    """Manages thrust allocation for manual or controller-based scenarios."""
    
    def __init__(self, lander, emergency_handler=None):
        self.lander = lander
        self.thrust_allocator = ThrustAllocator(lander.engines)
        self.emergency_handler = emergency_handler
    
    def allocate_from_controller(self, desired_accel: float, gravity: float, 
                                 thrust_vector: np.ndarray) -> np.ndarray:
        """
        Allocate thrust based on controller output.
        
        Args:
            desired_accel: Desired acceleration from controller (m/s^2)
            gravity: Current gravity (m/s^2)
            thrust_vector: Desired thrust direction (normalized)
            
        Returns:
            Array of per-engine thrust values (N)
        """
        # Calculate required thrust: F = m * (a_desired + g)
        # Ensure thrust is never negative (engines can't pull, only push)
        total_required = self.lander.mass * (desired_accel + gravity)
        total_required = max(0.0, total_required)  # Ensure non-negative
        
        # Normalize thrust vector
        thrust_vec = np.asarray(thrust_vector, dtype=float)
        thrust_vec = thrust_vec / (np.linalg.norm(thrust_vec) + 1e-12)
        desired_force_vec = thrust_vec * total_required
        desired_torque = np.zeros(3, dtype=float)
        
        # Allocate per-engine thrust magnitudes
        applied_thrusts = self.thrust_allocator.allocate(desired_force_vec, desired_torque)
        
        # Update engine throttles and get actual thrusts after applying emergency effects
        applied_thrusts = self._update_throttles_from_thrusts(applied_thrusts)
        
        return applied_thrusts
    
    def allocate_manual(self, thrust_force: float) -> np.ndarray:
        """
        Allocate thrust manually with equal distribution.
        
        Args:
            thrust_force: Total desired thrust (N)
            
        Returns:
            Array of per-engine thrust values (N)
        """
        thrust_force = float(thrust_force) if thrust_force is not None else 0.0
        thrust_force = min(thrust_force, self.lander.get_max_total_thrust())
        
        enabled_engines = [e for e in self.lander.engines if getattr(e, "enabled", True)]
        n_enabled = len(enabled_engines)
        
        if n_enabled == 0 or thrust_force <= 0.0:
            applied_thrusts = np.zeros(len(self.lander.engines), dtype=float)
            for engine in self.lander.engines:
                engine.throttle = 0.0
            return applied_thrusts
        
        # Equal distribution
        per_engine = thrust_force / n_enabled
        applied_thrusts = np.zeros(len(self.lander.engines), dtype=float)
        
        for i, engine in enumerate(self.lander.engines):
            if getattr(engine, "enabled", True):
                applied_thrusts[i] = per_engine
                max_thrust = float(getattr(engine, "max_thrust", per_engine))
                engine.throttle = per_engine / max_thrust if max_thrust > 0 else 0.0
            else:
                applied_thrusts[i] = 0.0
                engine.throttle = 0.0
        
        return applied_thrusts
    
    def _update_throttles_from_thrusts(self, thrusts: np.ndarray):
        """
        Update engine throttles based on allocated thrust values.
        
        Applies emergency scenario modifications (e.g., response lag) and returns
        the actual thrusts that result from the constrained throttles.
        
        Args:
            thrusts: Desired thrust values for each engine
            
        Returns:
            Actual thrust values (N) after applying any delays/constraints
        """
        actual_thrusts = np.zeros(len(self.lander.engines), dtype=float)
        
        for i, engine in enumerate(self.lander.engines):
            max_thrust = float(getattr(engine, "max_thrust", 0.0))
            if getattr(engine, "enabled", True) and max_thrust > 0.0:
                desired_throttle = float(thrusts[i] / max_thrust)
                # Apply emergency scenario modifications (e.g., response lag)
                if self.emergency_handler:
                    actual_throttle = self.emergency_handler.modify_throttle_command(i, desired_throttle)
                else:
                    actual_throttle = desired_throttle
                engine.throttle = actual_throttle
                # Calculate the actual thrust based on delayed throttle
                actual_thrusts[i] = actual_throttle * max_thrust
            else:
                engine.throttle = 0.0
                actual_thrusts[i] = 0.0
        
        return actual_thrusts
    
    def refresh_allocator(self):
        """Refresh allocator when engine configuration changes."""
        self.thrust_allocator = ThrustAllocator(self.lander.engines)

