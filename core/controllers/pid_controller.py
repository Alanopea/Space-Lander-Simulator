from typing import Optional, Tuple
from .IController import IController

class PIDController(IController):
    """Scalar PID controller with optional output limits and anti-windup."""

    def __init__(self, kp: float, ki: float, kd: float, setpoint: float = 0.0,
                 output_limits: Optional[Tuple[float, float]] = None):
        self.kp = float(kp)
        self.ki = float(ki)
        self.kd = float(kd)
        self.setpoint = float(setpoint)

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

    def update(self, measurement: float, dt: float) -> float:
        error = self.setpoint - float(measurement)
        # integral with simple anti-windup by clamping to reasonable range if limits provided
        self.integral += error * dt

        # derivative
        derivative = (error - self.prev_error) / dt if dt > 0 else 0.0

        raw_output = (self.kp * error) + (self.ki * self.integral) + (self.kd * derivative)
        output = self._clamp_output(raw_output)

        # anti-windup: if output saturated, prevent integral growing further
        if self._output_limits is not None and self.ki != 0.0:
            lo, hi = self._output_limits
            if (hi is not None and raw_output > hi) or (lo is not None and raw_output < lo):
                # back out integral increment
                self.integral -= error * dt

        self.prev_error = error
        return output