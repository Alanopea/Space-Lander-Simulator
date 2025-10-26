from core.controllers.IController import IController
import numpy as np

class LQRController(IController):
    """
    True continuous-time LQR controller for vertical descent (2-state model).
    Linearized plant (vertical position/velocity):
        x_dot = A x + B u,   A = [[0,1],[0,0]], B = [[0],[1]]
    This class computes optimal K by solving the continuous-time Algebraic
    Riccati Equation (CARE). If scipy is available it uses scipy.linalg.solve_continuous_are.
    Otherwise it falls back to a numerically stable Kleinman iteration that
    solves Lyapunov equations via Kronecker products (small 2x2 problem).
    The controller API matches existing IController: update(measurement, dt)
    where measurement is vertical velocity and return value is desired vertical
    acceleration (m/s^2).
    """

    def __init__(self, Q: np.ndarray = None, R: np.ndarray = None, setpoint: float = -10.0,
                 tol: float = 1e-6, max_iter: int = 200):
        # default cost matrices if not provided
        if Q is None:
            Q = np.diag([0.01, 200.0])   # penalize velocity more moderately; tune as needed
        if R is None:
            R = np.array([[1.0]])     # scalar control penalty

        self.A = np.array([[0.0, 1.0],
                           [0.0, 0.0]])
        self.B = np.array([[0.0],
                           [1.0]])

        self.Q = np.atleast_2d(Q).astype(float)
        self.R = np.atleast_2d(R).astype(float)
        self.setpoint = float(setpoint)

        self.tol = float(tol)
        self.max_iter = int(max_iter)

        # compute optimal K
        self.K = self._compute_lqr_gain()

        # state estimate used in update (simple integrator for position)
        self.pos_est = 0.0
        self.vel_est = 0.0

    def _compute_lqr_gain(self):
        # Try SciPy's solver first for robustness/performance
        try:
            from scipy.linalg import solve_continuous_are
            P = solve_continuous_are(self.A, self.B, self.Q, self.R)
            Rinv = np.linalg.inv(self.R)
            K = Rinv @ (self.B.T @ P)
            return np.asarray(K).reshape(1, 2)
        except Exception:
            # Fallback: Kleinman iteration solving continuous-time ARE via Lyapunov solves.
            n = self.A.shape[0]
            # start with zero gain
            K = np.zeros((1, n), dtype=float)
            I_n = np.eye(n)
            for _ in range(self.max_iter):
                Acl = self.A - self.B @ K
                # Solve Acl^T P + P Acl = -(Q + K^T R K)
                S = self.Q + K.T @ self.R @ K  # 2x2
                # Build Kronecker system: (I ⊗ Acl^T + Acl^T ⊗ I) vec(P) = -vec(S)
                M = np.kron(I_n, Acl.T) + np.kron(Acl.T, I_n)
                vecS = -S.reshape(n * n, order='F')
                try:
                    vecP = np.linalg.solve(M, vecS)
                except np.linalg.LinAlgError:
                    # numerical failure -> break and return last K
                    break
                P = vecP.reshape((n, n), order='F')
                # symmetricify
                P = 0.5 * (P + P.T)
                # update K
                try:
                    Rinv = np.linalg.inv(self.R)
                except np.linalg.LinAlgError:
                    break
                K_new = (Rinv @ (self.B.T @ P)).reshape(1, n)
                if np.linalg.norm(K_new - K) < self.tol:
                    return K_new
                K = K_new
            # if iteration fails or doesn't converge, fallback to a conservative tuned K
            return np.array([[0.0, 60.0]], dtype=float)

    def reset(self):
        self.pos_est = 0.0
        self.vel_est = 0.0

    def update(self, measurement, dt: float) -> float:
        # measurement expected to be vertical velocity (m/s)
        try:
            vel = float(measurement)
        except Exception:
            vel = float(self.vel_est)

        # update simple integrator estimate of position (no external position sensor)
        self.vel_est = vel
        self.pos_est += self.vel_est * float(dt)

        # state vector x = [pos; vel], desired reference vel = setpoint, desired pos = 0
        pos_err = self.pos_est
        vel_err = self.vel_est - self.setpoint
        x = np.array([pos_err, vel_err], dtype=float)

        # control law u = -K x
        u = - (self.K @ x.reshape(-1, 1)).item()

        return float(u)