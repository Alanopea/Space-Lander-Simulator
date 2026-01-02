# Centralized simulation defaults (controller, PID params, initial altitude)

DEFAULT_CONTROLLER_KIND = "mpc"   # "lqr" | "pid" | "mpc"
INITIAL_ALTITUDE = 1000.0        # meters (used by Dashboard / main entry)

# Centralized setpoint and initial velocity
LANDING_SETPOINT = -5.0          # desired vertical velocity at touchdown (m/s, negative = descending)
INITIAL_VELOCITY = -100.0         # starting vertical velocity (m/s) (positive = up)

# Velocity limits (safety/operational constraints)
# Controllers maintain setpoint continuously until landing - these are maximum allowed velocities
MAX_VERTICAL_VELOCITY = -5050.0    # Maximum descent velocity (m/s, negative = descending)
MIN_VERTICAL_VELOCITY = -0.2      # Minimum descent velocity (m/s, for safety margins)
MAX_HORIZONTAL_VELOCITY = 0.0    # Maximum horizontal velocity magnitude (m/s)

# PID defaults (used if controller kind == "pid")
# Output limits in m/s^2 (acceleration commands)
# Negative = deceleration (more thrust), positive = acceleration (less thrust)
# Range chosen to be comparable to LQR controller output range
# Tuned for smooth, stable velocity control without oscillation
# Note: Controller maintains setpoint continuously until landing - it does not turn off
# Upper limit set to allow smooth reduction but prevent negative thrust requirement
PID_DEFAULTS = {
    "kp": 0.6,  # Proportional gain - tuned so max error (-80 m/s) gives ~-48 m/s² (within limits)
    "ki": 0.01,  # Integral gain - very small to prevent overshoot while maintaining setpoint
    "kd": 3.0,  # Derivative gain - provides damping to prevent oscillation
    "setpoint": LANDING_SETPOINT,  # Target vertical velocity (maintained continuously)
    "output_limits": None #(-10.0, 5.0)  # Acceleration limits (m/s^2) - upper limit prevents zero thrust
}

# LQR defaults (used if controller kind == "lqr")
# Note: Controller maintains setpoint continuously until landing - it does not turn off
LQR_DEFAULTS = {
    "Q": None,  # Use LQRController internal defaults
    "R": None,  # Use LQRController internal defaults
    "setpoint": LANDING_SETPOINT  # Target vertical velocity (maintained continuously)
}

# MPC defaults (used if controller kind == "mpc")
# Note: Controller maintains setpoint continuously until landing - it does not turn off
MPC_DEFAULTS = {
    "setpoint": LANDING_SETPOINT,  # Target vertical velocity (maintained continuously)
    "horizon": 10,  # Prediction horizon (number of steps)
    "Q": None,  # Use MPCController internal defaults
    "R": None,  # Use MPCController internal defaults
    "output_limits": (-50.0, 20.0),  # Acceleration limits (m/s²)
    "dt_nom": 0.1  # Nominal time step for discretization (s)
}

def make_default_controller():
    """
    Create the default controller according to DEFAULT_CONTROLLER_KIND.
    Uses centralized defaults from PID_DEFAULTS, LQR_DEFAULTS, or MPC_DEFAULTS.
    """
    from core.controllers.controller_factory import make_controller
    
    if DEFAULT_CONTROLLER_KIND == "pid":
        return make_controller(kind="pid", **PID_DEFAULTS)
    elif DEFAULT_CONTROLLER_KIND == "lqr":
        return make_controller(kind="lqr", **LQR_DEFAULTS)
    elif DEFAULT_CONTROLLER_KIND == "mpc":
        return make_controller(kind="mpc", **MPC_DEFAULTS)
    else:
        # Fallback to LQR if unknown
        return make_controller(kind="lqr", **LQR_DEFAULTS)