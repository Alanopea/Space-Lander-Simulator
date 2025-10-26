# Centralized simulation defaults (controller, PID params, initial altitude)

DEFAULT_CONTROLLER_KIND = "lqr"   # "lqr" or "pid"
INITIAL_ALTITUDE = 1000.0        # meters (used by Dashboard / main entry)

# PID defaults (used if controller kind == "pid")
PID_DEFAULTS = {
    "kp": 300.0,
    "ki": 0.0,
    "kd": 120.0,
    "setpoint": -2.0,
    "output_limits": None
}

def make_default_controller():
    """
    Create the default controller according to DEFAULT_CONTROLLER_KIND.
    Extra kwargs are forwarded but current defaults are taken from PID_DEFAULTS.
    """
    from core.controllers.controller_factory import make_controller
    # pass both PID and LQR-friendly kwargs; factory ignores extras it doesn't need
    return make_controller(
        kind=DEFAULT_CONTROLLER_KIND,
        kp=PID_DEFAULTS["kp"],
        ki=PID_DEFAULTS["ki"],
        kd=PID_DEFAULTS["kd"],
        setpoint=PID_DEFAULTS["setpoint"],
        output_limits=PID_DEFAULTS["output_limits"],
        K=None
    )