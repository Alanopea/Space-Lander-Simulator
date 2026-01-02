from core.controllers.pid_controller import PIDController
from core.controllers.LQRController import LQRController

def make_controller(kind: str, **kwargs):
    """
    Factory for controllers.
    
    Args:
        kind: 'lqr' | 'pid' - controller type to create
        **kwargs: Arguments forwarded to the specific controller constructor
            For PID: kp, ki, kd, setpoint, output_limits
            For LQR: Q, R, setpoint
    
    Returns:
        IController: Configured controller instance
    
    Raises:
        ValueError: If kind is not 'lqr' or 'pid'
    """
    kind = kind.strip().lower() if kind else "lqr"
    
    if kind == "pid":
        return PIDController(
            kp=kwargs.get("kp"),
            ki=kwargs.get("ki"),
            kd=kwargs.get("kd"),
            setpoint=kwargs.get("setpoint"),
            output_limits=kwargs.get("output_limits")
        )
    elif kind == "lqr":
        return LQRController(
            Q=kwargs.get("Q"),
            R=kwargs.get("R"),
            setpoint=kwargs.get("setpoint")
        )
    else:
        raise ValueError(f"Unknown controller kind: {kind}. Must be 'lqr' or 'pid'")