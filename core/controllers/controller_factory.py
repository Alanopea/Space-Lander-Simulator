from core.controllers.pid_controller import PIDController
from core.controllers.LQRController import LQRController
from core.controllers.MPCController import MPCController

def make_controller(kind: str, **kwargs):
    """
    Factory for controllers.
    
    Args:
        kind: 'lqr' | 'pid' | 'mpc' - controller type to create
        **kwargs: Arguments forwarded to the specific controller constructor
            For PID: kp, ki, kd, setpoint, output_limits
            For LQR: Q, R, setpoint
            For MPC: setpoint, horizon, Q, R, output_limits, dt_nom
    
    Returns:
        IController: Configured controller instance
    
    Raises:
        ValueError: If kind is not 'lqr', 'pid', or 'mpc'
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
    elif kind == "mpc":
        return MPCController(
            setpoint=kwargs.get("setpoint"),
            horizon=kwargs.get("horizon"),
            Q=kwargs.get("Q"),
            R=kwargs.get("R"),
            output_limits=kwargs.get("output_limits"),
            dt_nom=kwargs.get("dt_nom")
        )
    else:
        raise ValueError(f"Unknown controller kind: {kind}. Must be 'lqr', 'pid', or 'mpc'")