from typing import Optional, Tuple
from .IController import IController

class PIDController(IController):
    """Scalar PID controller with optional output limits and anti-windup."""

    def __init__(self, kp: float, ki: float, kd: float, setpoint: float = 0.0,
                 output_limits: Optional[Tuple[float, float]] = None,
                 activation_altitude: float = 500.0):
        self.kp = float(kp)
        self.ki = float(ki)
        self.kd = float(kd)
        self.setpoint = float(setpoint)
        self.activation_altitude = float(activation_altitude)

        self.integral = 0.0
        self.prev_error = 0.0
        self._output_limits = output_limits  # (min, max) or None

    def reset(self):
        self.integral = 0.0
        self.prev_error = 0.0

    def _clamp_output(self, v: float) -> float:
        if self._output_limits is None:
            return v
        lo, hi = self._output_limits
        if lo is not None and v < lo:
            return lo
        if hi is not None and v > hi:
            return hi
        return v

    def update(self, measurement: float, dt: float, altitude: float = 0.0) -> float:
        """
        Update controller with new measurement.

        Args:
            measurement: Current velocity (m/s)
            dt: Time step (s)
            altitude: Current altitude (m) - optional, for compatibility

        Returns:
            Desired acceleration (m/s^2)
        """
        if dt <= 0.0:
            dt = 1e-6  # Avoid division by zero
        
        error = self.setpoint - float(measurement)
        
        # Calculate derivative term (using error derivative for smoother response)
        derivative = (error - self.prev_error) / dt
        
        # Calculate PID terms
        proportional = self.kp * error
        integral_term = self.ki * self.integral
        derivative_term = self.kd * derivative
        
        # Update integral (will be conditionally applied based on anti-windup)
        integral_increment = error * dt
        self.integral += integral_increment
        
        # Calculate raw output
        raw_output = proportional + integral_term + derivative_term
        
        # Clamp output to limits
        output = self._clamp_output(raw_output)
        
        # Anti-windup: if output saturated, prevent integral from accumulating
        if self._output_limits is not None and self.ki != 0.0:
            lo, hi = self._output_limits
            saturated = (hi is not None and raw_output > hi) or (lo is not None and raw_output < lo)
            if saturated:
                # Back out the integral increment we just added to prevent windup
                self.integral -= integral_increment
            else:
                # Also limit integral magnitude to prevent excessive buildup during small errors
                # This helps prevent oscillations around the setpoint
                max_integral_magnitude = abs((hi - lo) / (self.ki + 1e-9)) * 0.5  # Conservative limit
                if abs(self.integral) > max_integral_magnitude:
                    self.integral = max_integral_magnitude if self.integral > 0 else -max_integral_magnitude

        self.prev_error = error
        return output