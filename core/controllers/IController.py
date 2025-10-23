from abc import ABC, abstractmethod

class IController(ABC):
    @abstractmethod
    def update(self, measurement, dt):
        raise NotImplementedError
    
    def reset(self):
        return
