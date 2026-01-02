from abc import ABC, abstractmethod

class IController(ABC):
    @abstractmethod
    def update(self, measurement, dt):
        """Update controller with new measurement and return control output."""
        raise NotImplementedError
    
    @abstractmethod
    def reset(self):
        """Reset controller internal state."""
        raise NotImplementedError
