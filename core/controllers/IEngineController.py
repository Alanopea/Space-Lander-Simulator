# Engine-level controller interface. Per‑engine controller contract.

from abc import ABC, abstractmethod

class IEngineController(ABC):
    
    @abstractmethod
    def update(self, required_thrust_N, engine, dt):
        raise NotImplementedError
