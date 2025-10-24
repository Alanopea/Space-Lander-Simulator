import numpy as np

class Engine:
    """Lightweight engine representation."""
    def __init__(self, max_thrust: float, position: np.ndarray, direction: np.ndarray):
        self.max_thrust = float(max_thrust)
        self.position = np.asarray(position, dtype=float)  # vector from COM to mount (m)
        dirv = np.asarray(direction, dtype=float)
        norm = np.linalg.norm(dirv)
        self.direction = dirv / norm if norm > 0 else np.array([0.0, 1.0, 0.0])
        self.enabled = True
        self.throttle = 0.0  # 0..1

    @property
    def current_thrust(self) -> float:
        return self.max_thrust * self.throttle if self.enabled else 0.0