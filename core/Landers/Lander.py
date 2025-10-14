import numpy as np
from abc import ABC, abstractmethod

class Lander(ABC):
    """
    Abstract lander model (cuboid approximation).
    - dry_mass: kg (structure + payload)
    - max_fuel_mass: kg
    - thrust_per_engine: N
    - engine_count: int
    - drag_coefficient: scalar
    - planet: Planet instance
    - dimensions: (width, height, depth) in meters (cuboid)
    """

    def __init__(self, dry_mass, max_fuel_mass, thrust_per_engine, engine_count,
                 drag_coefficient, planet, dimensions):
        self.dry_mass = float(dry_mass)
        self.max_fuel_mass = float(max_fuel_mass)
        self.fuel_mass = float(max_fuel_mass)   # start full by default

        self.thrust_per_engine = float(thrust_per_engine)
        self.engine_count = int(engine_count)
        self.engine_status = [True] * self.engine_count

        self.drag_coefficient = float(drag_coefficient)
        self.planet = planet
        self.dimensions = np.array(dimensions, dtype=float)  # width, height, depth

        # dynamic state
        self.position = np.array([0.0, 1000.0, 0.0])
        self.velocity = np.array([0.0, 0.0, 0.0])
        self.orientation = np.array([0.0, 0.0, 0.0])       # Euler angles (rad)
        self.angular_velocity = np.array([0.0, 0.0, 0.0])  # rad/s

    @property
    def mass(self):
        """Total mass = dry_mass + current fuel mass."""
        return self.dry_mass + self.fuel_mass

    @property
    def inertia(self):
        """Approximate diagonal inertia for cuboid aligned with axes."""
        w, h, d = self.dimensions
        m = self.mass
        return (1.0 / 12.0) * m * np.array([h**2 + d**2, w**2 + d**2, w**2 + h**2])

    def get_active_engine_count(self):
        return sum(1 for s in self.engine_status if s)

    def get_total_thrust(self):
        """Total available thrust with currently active engines at full throttle (N)."""
        return self.thrust_per_engine * self.get_active_engine_count()

    def set_engine_status(self, index, enabled: bool):
        if 0 <= index < self.engine_count:
            self.engine_status[index] = bool(enabled)

    def fail_engine(self, index):
        self.set_engine_status(index, False)

    def repair_engine(self, index):
        self.set_engine_status(index, True)

    def consume_fuel(self, amount_kg):
        """Consume fuel (kg). Returns actual consumed."""
        consumed = min(self.fuel_mass, max(0.0, float(amount_kg)))
        self.fuel_mass -= consumed
        return consumed

    def reset_fuel(self):
        self.fuel_mass = float(self.max_fuel_mass)

    def telemetry_extras(self):
        """Return extras dict suitable for UI telemetry (mass, fuel)."""
        return {
            "total_mass": float(self.mass),
            "fuel_mass": float(self.fuel_mass),
            "max_fuel_mass": float(self.max_fuel_mass)
        }

    @abstractmethod
    def get_name(self):
        raise NotImplementedError
