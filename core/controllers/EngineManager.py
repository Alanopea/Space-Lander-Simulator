# Allocate a requested thrust across engines (use per-engine controllers if provided).

from typing import Dict, Optional
from core.controllers.IEngineController import IEngineController

class EngineManager:
    def __init__(self, lander, per_engine_controllers: Optional[Dict[int, IEngineController]] = None):
        self.lander = lander
        self.controllers = per_engine_controllers or {}

    def allocate(self, required_thrust_N: float, dt: float = 0.0) -> float:
        # clamp to available capacity
        total_available = self.lander.get_max_total_thrust()
        required = max(0.0, min(required_thrust_N, total_available))

        if not self.controllers:
            return self.lander.allocate_thrust_equal(required)

        # controllers present -> ask each for throttle, then fill remaining equally
        for idx, engine in enumerate(self.lander.engines):
            if not engine.enabled:
                engine.throttle = 0.0
                continue
            ctrl = self.controllers.get(idx)
            if ctrl is not None:
                try:
                    engine.throttle = max(0.0, min(1.0, float(ctrl.update(required, engine, dt))))
                except Exception:
                    engine.throttle = 0.0
            else:
                engine.throttle = 0.0

        applied = sum(e.current_thrust for e in self.lander.engines)
        remaining = required - applied
        uncontrolled = [e for i,e in enumerate(self.lander.engines) if e.enabled and i not in self.controllers]
        if remaining > 1e-6 and uncontrolled:
            per = remaining / len(uncontrolled)
            for e in uncontrolled:
                e.throttle = min(1.0, per / e.max_thrust)
        return sum(e.current_thrust for e in self.lander.engines)