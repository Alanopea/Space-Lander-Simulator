"""Fuel consumption and management logic."""

import numpy as np

class FuelManager:
    """Manages fuel consumption based on engine thrust."""
    
    STANDARD_GRAVITY = 9.80665  # m/s^2
    
    def __init__(self, lander):
        self.lander = lander
    
    def consume_fuel_for_thrusts(self, applied_thrusts: np.ndarray, dt: float) -> np.ndarray:
        """
        Calculate and consume fuel for given thrusts, scaling down if insufficient fuel.
        
        Args:
            applied_thrusts: Array of per-engine thrust values (N)
            dt: Time step (s)
            
        Returns:
            Updated applied_thrusts array after fuel constraints applied
        """
        if applied_thrusts is None or len(applied_thrusts) == 0:
            return np.zeros(0, dtype=float)
        
        total_thrust = float(np.sum(applied_thrusts))
        if total_thrust <= 0.0:
            return applied_thrusts
        
        # Calculate mass flow using per-engine specific impulse
        mass_flow = self._calculate_mass_flow(applied_thrusts)
        
        if mass_flow <= 0.0:
            return applied_thrusts
        
        fuel_needed = mass_flow * dt
        
        # Handle fuel constraints
        if self.lander.fuel_mass <= 0.0:
            # No fuel - zero all throttles
            self._zero_all_throttles()
            return np.zeros_like(applied_thrusts)
        
        if fuel_needed > self.lander.fuel_mass:
            # Insufficient fuel - scale down thrusts proportionally
            scale = self.lander.fuel_mass / fuel_needed
            scaled_thrusts = applied_thrusts * scale
            self._update_throttles_from_thrusts(scaled_thrusts)
            self.lander.consume_fuel(self.lander.fuel_mass, dt)
            return scaled_thrusts
        else:
            # Enough fuel - consume normally
            self.lander.consume_fuel(fuel_needed, dt)
            return applied_thrusts
    
    def _calculate_mass_flow(self, applied_thrusts: np.ndarray) -> float:
        """Calculate total mass flow rate for given thrusts."""
        mass_flow = 0.0
        for i, thrust_i in enumerate(applied_thrusts):
            if thrust_i <= 0.0:
                continue
            
            engine = self.lander.engines[i]
            isp = float(getattr(engine, "specific_impulse", 
                               getattr(self.lander, "specific_impulse", 300.0)))
            
            if isp > 0.0:
                mass_flow += thrust_i / (isp * self.STANDARD_GRAVITY)
        
        return mass_flow
    
    def _zero_all_throttles(self):
        """Set all engine throttles to zero."""
        for engine in self.lander.engines:
            engine.throttle = 0.0
    
    def _update_throttles_from_thrusts(self, thrusts: np.ndarray):
        """Update engine throttles based on thrust values."""
        for i, engine in enumerate(self.lander.engines):
            max_thrust = float(getattr(engine, "max_thrust", 0.0))
            engine.throttle = (thrusts[i] / max_thrust) if max_thrust > 0 else 0.0

