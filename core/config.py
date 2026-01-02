# Centralized simulation defaults (controller, PID params, initial altitude)

DEFAULT_CONTROLLER_KIND = "lqr"   # "lqr" or "pid"
INITIAL_ALTITUDE = 1000.0        # meters (used by Dashboard / main entry)

# Centralized setpoint and initial velocity
LANDING_SETPOINT = -20.0          # desired vertical velocity at touchdown (m/s, negative = descending)
INITIAL_VELOCITY = -100.0         # starting vertical velocity (m/s) (positive = up)

# PID defaults (used if controller kind == "pid")
PID_DEFAULTS = {
    "kp": 300.0,
    "ki": 0.0,
    "kd": 120.0,
    "setpoint": LANDING_SETPOINT,
    "output_limits": None
}

# LQR defaults (used if controller kind == "lqr")
LQR_DEFAULTS = {
    "Q": None,  # Use LQRController internal defaults
    "R": None,  # Use LQRController internal defaults
    "setpoint": LANDING_SETPOINT
}

def make_default_controller():
    """
    Create the default controller according to DEFAULT_CONTROLLER_KIND.
    Uses centralized defaults from PID_DEFAULTS or LQR_DEFAULTS.
    """
    from core.controllers.controller_factory import make_controller
    
    if DEFAULT_CONTROLLER_KIND == "pid":
        return make_controller(kind="pid", **PID_DEFAULTS)
    else:
        return make_controller(kind="lqr", **LQR_DEFAULTS)