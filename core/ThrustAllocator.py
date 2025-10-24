import numpy as np

class ThrustAllocator:
    """
    Allocate desired total force and torque to per-engine thrust commands.
    - engines: list of Engine objects (with .position, .direction, .max_thrust, .enabled)
    - allocate(desired_force, desired_torque) -> np.array of per-engine thrust magnitudes (N)
    """

    def __init__(self, engines):
        self.engines = engines

    def allocate(self, desired_force: np.ndarray, desired_torque: np.ndarray):
        """
        Solve A x = b in least-squares sense with clipping to bounds [0, max_thrust_i].
        A is 6 x n: [f_dirs; cross(r_i, f_dir)] where f_dirs are 3x1 columns and r_i is position.
        desired_force, desired_torque are length-3 vectors.
        Returns applied thrust array length n.
        """
        n = len(self.engines)
        if n == 0:
            return np.zeros(0, dtype=float)

        # Build A matrix
        f_dirs = np.column_stack([e.direction for e in self.engines])  # 3 x n
        torques = np.column_stack([np.cross(e.position, e.direction) for e in self.engines])  # 3 x n

        A = np.vstack([f_dirs, torques])  # 6 x n
        b = np.hstack([np.asarray(desired_force, dtype=float), np.asarray(desired_torque, dtype=float)])  # 6

        # Solve least squares A x = b
        # Weighted least-squares could be added. Use numpy.linalg.lstsq
        try:
            x, *_ = np.linalg.lstsq(A, b, rcond=None)
        except Exception:
            # fallback zeros
            x = np.zeros(n, dtype=float)

        # Enforce non-negative and respect disabled engines
        max_thrusts = np.array([e.max_thrust if e.enabled else 0.0 for e in self.engines], dtype=float)
        x = np.clip(x, 0.0, max_thrusts)

        # If clipping removed force, distribute residual greedily among available engines
        applied = x.copy()
        # compute residual
        residual = b - A @ applied
        resid_norm = np.linalg.norm(residual)
        if resid_norm > 1e-6:
            # attempt to iteratively distribute remaining required force magnitude along directions
            # compute remaining capacity
            capacity = max_thrusts - applied
            total_capacity = np.sum(capacity)
            if total_capacity > 1e-9:
                # project residual force onto summed engine directions to get scalar to distribute
                # compute per-engine weights proportional to capacity * alignment with residual force
                force_part = desired_force  # prioritize force match
                dir_align = np.maximum(0.0, (f_dirs.T @ force_part))  # n
                weights = dir_align * capacity
                if np.sum(weights) <= 1e-12:
                    # No engine can produce force in the desired direction -> cannot satisfy opposing request.
                    # Leave applied as-is (it was already clipped); do not distribute positive thrust to satisfy
                    # a desired force that points opposite to available engine directions.
                    applied = np.clip(applied, 0.0, max_thrusts)
                else:
                    weights = weights / np.sum(weights)
                    add = weights * min(np.linalg.norm(force_part), total_capacity)  # heuristic
                    applied += add
                    applied = np.minimum(applied, max_thrusts)

        # Ensure valid final throttles
        applied = np.clip(applied, 0.0, max_thrusts)
        return applied