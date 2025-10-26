from core.controllers.PIDConfig import make_pid
from core.controllers.LQRController import LQRController

def make_controller(kind: str = "lqr", **kwargs):
    """
    Factory for controllers.
    kind: 'lqr' | 'pid'
    kwargs are forwarded to the specific constructor/factory.
    Default: LQR controller.
    """
    kind = (kind or "lqr").strip().lower()
    if kind == "pid":
        return make_pid(
            kp=kwargs.get("kp", 300.0),
            ki=kwargs.get("ki", 0.0),
            kd=kwargs.get("kd", 120.0),
            setpoint=kwargs.get("setpoint", -10.0),
            output_limits=kwargs.get("output_limits", None)
        )

    # Build LQR with optional Q, R, setpoint
    Q = kwargs.get("Q", None)
    R = kwargs.get("R", None)
    setpoint = kwargs.get("setpoint", -10.0)
    return LQRController(Q=Q, R=R, setpoint=setpoint)