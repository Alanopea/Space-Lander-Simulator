import numpy as np
from abc import ABC, abstractmethod
from core.Landers.Engine import Engine

class Lander(ABC):
    """
    Abstract lander model (cuboid approximation) with engine mounts and per-engine state.
    Subclasses should call super().__init__ and may override engine_mounts or call
    configure_engines(...) to set mount positions and directions.
    """
    def __init__(self, dry_mass, max_fuel_mass, thrust_per_engine, engine_count,
                 drag_coefficient, planet, dimensions):
        self.dry_mass = float(dry_mass)
        self.max_fuel_mass = float(max_fuel_mass)
        self.fuel_mass = float(max_fuel_mass)   # start full by default
        
        # Fuel consumption tracking
        self.fuel_consumption_rate = 0.0  # kg/s

        self.thrust_per_engine = float(thrust_per_engine)
        self.engine_count = int(engine_count)

        self.drag_coefficient = float(drag_coefficient)
        self.planet = planet
        self.dimensions = np.array(dimensions, dtype=float)  # width, height, depth

        # dynamic state
        self.position = np.array([0.0, 1000.0, 0.0])
        self.velocity = np.array([0.0, 0.0, 0.0])
        self.orientation = np.array([0.0, 0.0, 0.0])       # Euler angles (rad)
        self.angular_velocity = np.array([0.0, 0.0, 0.0])  # rad/s

        # propulsion defaults
        self.specific_impulse = 300.0

        # Setup engines with default simple layout (centered engines pointing up).
        # Subclasses may call configure_engines(...) to provide real mounts.
        self.engines = []
        self.configure_default_engines(thrust_per_engine, engine_count)

    @property
    def mass(self):
        return self.dry_mass + self.fuel_mass

    @property
    def inertia(self):
        w, h, d = self.dimensions
        m = self.mass
        return (1.0 / 12.0) * m * np.array([h**2 + d**2, w**2 + d**2, w**2 + h**2])

    # --- engine management helpers ---
    def configure_default_engines(self, thrust_per_engine: float, engine_count: int):
        """Create engine_count engines located under the vehicle center, pointing up."""
        self.engines = []
        for i in range(engine_count):
            pos = np.array([0.0, -self.dimensions[1] / 2.0, 0.0])  # bottom center
            dirv = np.array([0.0, 1.0, 0.0])  # upward
            self.engines.append(Engine(thrust_per_engine, pos, dirv))

    def configure_engines(self, positions, directions, max_thrusts=None):
        """Configure engines with arrays of positions and directions. lengths must match."""
        positions = [np.asarray(p, dtype=float) for p in positions]
        directions = [np.asarray(d, dtype=float) for d in directions]
        n = len(positions)
        self.engines = []
        for i in range(n):
            mt = float(max_thrusts[i]) if (max_thrusts is not None and i < len(max_thrusts)) else self.thrust_per_engine
            self.engines.append(Engine(mt, positions[i], directions[i]))

    def get_active_engine_count(self):
        return sum(1 for e in self.engines if e.enabled)

    def get_max_total_thrust(self):
        return sum(e.max_thrust for e in self.engines if e.enabled)

    def get_total_thrust(self):
        return sum(e.current_thrust for e in self.engines)

    def set_engine_enabled(self, index: int, enabled: bool):
        if 0 <= index < len(self.engines):
            self.engines[index].enabled = bool(enabled)
            if not enabled:
                self.engines[index].throttle = 0.0

    def set_engine_throttle(self, index: int, throttle: float):
        if 0 <= index < len(self.engines):
            self.engines[index].throttle = float(max(0.0, min(1.0, throttle)))

    def set_all_throttles(self, throttle: float):
        for e in self.engines:
            if e.enabled:
                e.throttle = float(max(0.0, min(1.0, throttle)))

    def allocate_thrust_equal(self, required_thrust: float):
        """Legacy equal allocation among enabled engines."""
        enabled = [e for e in self.engines if e.enabled]
        if not enabled:
            return 0.0
        per = required_thrust / len(enabled)
        total = 0.0
        for e in enabled:
            e.throttle = min(1.0, per / e.max_thrust)
            total += e.current_thrust
        return total

    # --- fuel & telemetry ---
    def consume_fuel(self, amount_kg, dt=0.0):
        """
        Consume fuel and update consumption rate.
        
        Args:
            amount_kg: Amount of fuel to consume (kg)
            dt: Time step (s) - used to calculate consumption rate
        """
        consumed = min(self.fuel_mass, max(0.0, float(amount_kg)))
        self.fuel_mass -= consumed
        
        # Update fuel consumption rate (kg/s)
        if dt > 0.0:
            self.fuel_consumption_rate = consumed / dt
        else:
            self.fuel_consumption_rate = 0.0
        
        return consumed

    def reset_fuel(self):
        self.fuel_mass = float(self.max_fuel_mass)
        self.fuel_consumption_rate = 0.0

    def telemetry_extras(self):
        return {
            "total_mass": float(self.mass),
            "dry_mass": float(self.dry_mass),
            "fuel_mass": float(self.fuel_mass),
            "max_fuel_mass": float(self.max_fuel_mass),
            "fuel_consumption_rate": float(self.fuel_consumption_rate),  # kg/s
            "fuel_percentage": (self.fuel_mass / self.max_fuel_mass * 100.0) if self.max_fuel_mass > 0 else 0.0,
            "engine_count": len(self.engines),
            "per_engine_thrust": [float(e.current_thrust) for e in self.engines],
            "per_engine_enabled": [bool(e.enabled) for e in self.engines],
            "per_engine_max_thrust": [float(e.max_thrust) for e in self.engines]
        }

    @abstractmethod
    def get_name(self):
        raise NotImplementedError
