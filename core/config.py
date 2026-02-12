# Centralized simulation defaults (controller, PID params, initial altitude)

DEFAULT_CONTROLLER_KIND = "mpc"   # "lqr" | "pid" | "mpc"
INITIAL_ALTITUDE = 1000.0        # meters (fallback default, used when planet doesn't specify)
INITIAL_VELOCITY = -20.0         # starting vertical velocity (m/s) (fallback default, used when planet doesn't specify)

# Centralized setpoint and initial velocity
LANDING_SETPOINT = -3.0          # desired vertical velocity at touchdown (m/s, negative = descending)

# Velocity limits (safety/operational constraints)
# Controllers maintain setpoint continuously until landing - these are maximum allowed velocities
MAX_VERTICAL_VELOCITY = -5050.0    # Maximum descent velocity (m/s, negative = descending)
MIN_VERTICAL_VELOCITY = -3.0      # Minimum descent velocity (m/s, for safety margins)
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
    "output_limits": (-10.0, 5.0),  # Acceleration limits (m/s^2) - upper limit prevents zero thrust
    "activation_altitude": 500.0  # Controller activates below this altitude (m)
}

# LQR defaults (used if controller kind == "lqr")
# Note: Controller maintains setpoint continuously until landing - it does not turn off
LQR_DEFAULTS = {
    "Q": None,  # Use LQRController internal defaults
    "R": None,  # Use LQRController internal defaults
    "setpoint": LANDING_SETPOINT,  # Target vertical velocity (maintained continuously)
    "activation_altitude": 500.0  # Controller activates below this altitude (m)
}

# MPC defaults (used if controller kind == "mpc")
# Note: Controller maintains setpoint continuously until landing - it does not turn off
MPC_DEFAULTS = {
    "setpoint": LANDING_SETPOINT,  # Target vertical velocity (maintained continuously)
    "horizon": 10,  # Prediction horizon (number of steps)
    "Q": None,  # Use MPCController internal defaults
    "R": None,  # Use MPCController internal defaults
    "output_limits": (-50.0, 20.0),  # Acceleration limits (m/s²)
    "dt_nom": 0.1,  # Nominal time step for discretization (s)
    "activation_altitude": 1000.0,  # Controller activates below this altitude (m)
    "gravity": 9.81  # Gravity acceleration (m/s²)
}

def get_initial_altitude(planet=None):
    """
    Get initial altitude for a planet. Returns planet-specific value if available,
    otherwise returns the default fallback value.
    
    Args:
        planet: Planet instance (optional)
    
    Returns:
        float: Initial altitude in meters
    """
    if planet is not None and hasattr(planet, 'initial_altitude') and planet.initial_altitude is not None:
        return planet.initial_altitude
    return INITIAL_ALTITUDE


def get_initial_velocity(planet=None):
    """
    Get initial velocity for a planet. Returns planet-specific value if available,
    otherwise returns the default fallback value.
    
    Args:
        planet: Planet instance (optional)
    
    Returns:
        float: Initial velocity in m/s
    """
    if planet is not None and hasattr(planet, 'initial_velocity') and planet.initial_velocity is not None:
        return planet.initial_velocity
    return INITIAL_VELOCITY


def make_controller_by_kind(kind=None):
    """
    Create a controller by kind. If kind is None, uses DEFAULT_CONTROLLER_KIND.
    Uses centralized defaults from PID_DEFAULTS, LQR_DEFAULTS, or MPC_DEFAULTS.
    
    Args:
        kind: Controller kind ("pid", "lqr", "mpc") or None for default
    
    Returns:
        IController: Configured controller instance
    """
    from core.controllers.controller_factory import make_controller
    
    if kind is None:
        kind = DEFAULT_CONTROLLER_KIND
    
    kind = kind.strip().lower() if kind else DEFAULT_CONTROLLER_KIND
    
    if kind == "pid":
        return make_controller(kind="pid", **PID_DEFAULTS)
    elif kind == "lqr":
        return make_controller(kind="lqr", **LQR_DEFAULTS)
    elif kind == "mpc":
        return make_controller(kind="mpc", **MPC_DEFAULTS)
    else:
        # Fallback to default if unknown
        return make_controller_by_kind(DEFAULT_CONTROLLER_KIND)


def make_default_controller():
    """
    Create the default controller according to DEFAULT_CONTROLLER_KIND.
    Uses centralized defaults from PID_DEFAULTS, LQR_DEFAULTS, or MPC_DEFAULTS.
    """
    return make_controller_by_kind(None)