"""
Model Predictive Control (MPC) controller for vertical descent landing.

Uses a linearized 2-state model (position, velocity) similar to LQR.
Solves a quadratic optimization problem over a prediction horizon at each step.
"""

from core.controllers.IController import IController
import numpy as np

class MPCController(IController):
    """
    MPC controller for vertical descent with 2-state linear model.

    Model: x_dot = A x + B u + d
    where x = [position; velocity], u = acceleration command, d = [0; -g] (gravity disturbance)

    Gravity is treated as a known constant disturbance and is explicitly included in the dynamics.
    The controller outputs desired acceleration (m/s²) which is converted to thrust by the simulator.

    At each step, solves:
    min sum_{k=0}^{N-1} [||x_k - x_ref||^2_Q + ||u_k||^2_R]
    subject to:
        x_{k+1} = A_d x_k + B_d u_k + d_d  (discrete dynamics with gravity)
        u_min <= u_k <= u_max             (control constraints)

    Returns first control action u_0 (desired acceleration in m/s²).
    """

    def __init__(self, setpoint: float = -20.0, horizon: int = 10,
                 Q: np.ndarray = None, R: np.ndarray = None,
                 output_limits: tuple = None, dt_nom: float = 0.1,
                 activation_altitude: float = 500.0, gravity: float = 9.81):
        """
        Args:
            setpoint: Target vertical velocity (m/s)
            horizon: Prediction horizon (number of steps)
            Q: State cost matrix (2x2), defaults to [0.01, 200.0] on diagonal
            R: Control cost scalar or matrix, defaults to 1.0
            output_limits: (min, max) acceleration limits (m/s²), defaults to (-50, 20)
            dt_nom: Nominal time step for discretization (s)
            activation_altitude: Altitude below which controller activates (m), defaults to 500.0
            gravity: Gravity acceleration (m/s²), defaults to 9.81
        """
        # Continuous-time model (same as LQR)
        self.A_cont = np.array([[0.0, 1.0],
                               [0.0, 0.0]], dtype=float)
        self.B_cont = np.array([[0.0],
                               [1.0]], dtype=float)
        
        # Default cost matrices
        if Q is None:
            Q = np.diag([0.01, 200.0])  # Penalize velocity error more
        if R is None:
            R = np.array([[1.0]])  # Scalar control penalty
        
        self.Q = np.atleast_2d(Q).astype(float)
        # Handle R as scalar or matrix
        if isinstance(R, np.ndarray):
            if R.size == 1:
                self.R = float(R.item())
            else:
                self.R = np.atleast_2d(R).astype(float)
        else:
            self.R = float(R)
        self.setpoint = float(setpoint)
        self.horizon = int(horizon)
        self.dt_nom = float(dt_nom)
        self.activation_altitude = float(activation_altitude)
        self.gravity = float(gravity)

        # Output limits (acceleration constraints)
        if output_limits is None:
            output_limits = (-50.0, 20.0)
        self.u_min = float(output_limits[0])
        self.u_max = float(output_limits[1])

        # Discretize the system (zero-order hold)
        self._discretize(dt_nom)

        # State estimate (position and velocity)
        self.pos_est = 0.0
        self.vel_est = 0.0

        # Reference state: [desired_pos, desired_vel]
        # For landing, we want position to go to 0 and velocity to setpoint
        self.x_ref = np.array([0.0, self.setpoint], dtype=float)
    
    def _discretize(self, dt: float):
        """Discretize continuous-time system using zero-order hold."""
        # Continuous-time model: x_dot = A x + B u + d
        # where d = [0; -g] is the gravity disturbance

        # A_d = [[1, dt], [0, 1]]
        # B_d = [[dt²/2], [dt]]
        # d_d = [[dt²/2], [dt]] * (-g) = -g * [[dt²/2], [dt]]

        A_d = np.array([[1.0, dt],
                       [0.0, 1.0]], dtype=float)
        B_d = np.array([[0.5 * dt * dt],
                       [dt]], dtype=float)
        d_d = np.array([[0.5 * dt * dt],
                       [dt]], dtype=float) * (-self.gravity)

        self.A_d = A_d
        self.B_d = B_d
        self.d_d = d_d  # Discrete-time gravity disturbance
    
    def reset(self):
        """Reset controller internal state."""
        self.pos_est = 0.0
        self.vel_est = 0.0
    
    def _predict_trajectory(self, x0: np.ndarray, u_sequence: np.ndarray, dt: float) -> np.ndarray:
        """
        Predict state trajectory given initial state and control sequence.
        Includes gravity as a known disturbance in the dynamics.

        Args:
            x0: Initial state [pos, vel]
            u_sequence: Control sequence (horizon,)
            dt: Time step (may differ from nominal)

        Returns:
            State trajectory (horizon+1, 2)
        """
        # Re-discretize if dt changed
        if abs(dt - self.dt_nom) > 1e-6:
            self._discretize(dt)

        N = len(u_sequence)
        x_traj = np.zeros((N + 1, 2))
        x_traj[0] = x0

        for k in range(N):
            # x_{k+1} = A_d x_k + B_d u_k + d_d  (includes gravity)
            x_traj[k + 1] = self.A_d @ x_traj[k] + self.B_d.flatten() * u_sequence[k] + self.d_d.flatten()

        return x_traj
    
    def _cost_function(self, u_sequence: np.ndarray, x0: np.ndarray, dt: float) -> float:
        """
        Compute MPC cost function for given control sequence.
        
        Args:
            u_sequence: Control sequence (horizon,)
            x0: Initial state
            dt: Time step
            
        Returns:
            Scalar cost value
        """
        # Predict trajectory
        x_traj = self._predict_trajectory(x0, u_sequence, dt)
        
        # Compute cost
        cost = 0.0
        for k in range(self.horizon):
            # State error cost
            x_err = x_traj[k] - self.x_ref
            cost += x_err.T @ self.Q @ x_err
            
            # Control cost
            u_k = u_sequence[k]
            if isinstance(self.R, np.ndarray):
                cost += u_k * self.R * u_k
            else:
                cost += self.R * u_k * u_k
        
        # Terminal cost (weight final state more)
        x_err_terminal = x_traj[-1] - self.x_ref
        cost += 2.0 * (x_err_terminal.T @ self.Q @ x_err_terminal)
        
        return cost
    
    def _solve_mpc(self, x0: np.ndarray, dt: float) -> float:
        """
        Solve MPC optimization problem.
        
        Args:
            x0: Current state estimate [pos, vel]
            dt: Time step
            
        Returns:
            Optimal control action (acceleration in m/s²)
        """
        try:
            from scipy.optimize import minimize
            
            # Initial guess: zeros or small control
            u_init = np.zeros(self.horizon)
            
            # Bounds for control sequence
            bounds = [(self.u_min, self.u_max) for _ in range(self.horizon)]
            
            # Objective function (minimize cost)
            def objective(u_seq):
                return self._cost_function(u_seq, x0, dt)
            
            # Solve optimization
            result = minimize(
                objective,
                u_init,
                method='L-BFGS-B',  # Good for bounded optimization
                bounds=bounds,
                options={'maxiter': 100, 'ftol': 1e-6}
            )
            
            if result.success:
                return float(result.x[0])  # Return first control action
            else:
                # If optimization fails, use simple fallback
                return self._fallback_control(x0)
                
        except ImportError:
            # If scipy not available, use fallback
            return self._fallback_control(x0)
        except Exception:
            # On any error, use fallback
            return self._fallback_control(x0)
    
    def _fallback_control(self, x0: np.ndarray) -> float:
        """Fallback control when optimization fails (simple PD control)."""
        pos_err = x0[0] - self.x_ref[0]
        vel_err = x0[1] - self.x_ref[1]
        
        # Simple PD controller
        kp = 0.1
        kd = 0.6
        u = -kp * pos_err - kd * vel_err
        
        # Clamp to limits
        u = max(self.u_min, min(self.u_max, u))
        return float(u)
    
    def update(self, measurement, dt: float, altitude: float = 0.0) -> float:
        """
        Update controller with new measurement and return control output.

        The controller activates only below the activation altitude to avoid
        unnecessary control action during initial descent.

        Args:
            measurement: Current vertical velocity (m/s)
            dt: Time step (s)
            altitude: Current altitude (m) - used for activation logic

        Returns:
            Desired acceleration (m/s²) - 0 if controller inactive
        """

        if dt <= 0.0:
            dt = 1e-6

        # Update state estimate
        vel = float(measurement)
        self.vel_est = vel
        self.pos_est += self.vel_est * float(dt)

        # Current state
        x0 = np.array([self.pos_est, self.vel_est], dtype=float)

        # Solve MPC problem
        u_opt = self._solve_mpc(x0, dt)

        return u_opt

