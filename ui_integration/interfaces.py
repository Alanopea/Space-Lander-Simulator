from abc import ABC, abstractmethod

class IController(ABC):
    @abstractmethod
    def update(self, measurement, dt):
        """Return control output given measurement and dt."""
        raise NotImplementedError

class ISimulator(ABC):
    @abstractmethod
    def reset(self):
        """Reset simulation to initial state."""
        raise NotImplementedError

    @abstractmethod
    def step(self, dt):
        """Advance simulation by dt. Return telemetry dict.
        Example return: {'time': t, 'position': np.array, 'velocity': np.array, 'orientation': np.array, 'status': 'DESCENDING'}"""
        raise NotImplementedError

    @abstractmethod
    def get_logger(self):
        """Return the DataLogger instance (optional)."""
        raise NotImplementedError