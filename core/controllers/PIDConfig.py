from core.controllers.pid_controller import PIDController

def make_pid(kp: float = 300.0,
             ki: float = 0.0,
             kd: float = 120.0,
             setpoint: float = -2.0,
             output_limits: tuple = None) -> PIDController:
    """
    Return a configured PIDController instance.
    Centralizes PID tuning so all callers use the same defaults.
    Override args to customize per-run.
    """
    if output_limits is not None:
        return PIDController(kp=kp, ki=ki, kd=kd, setpoint=setpoint, output_limits=output_limits)
    return PIDController(kp=kp, ki=ki, kd=kd, setpoint=setpoint)