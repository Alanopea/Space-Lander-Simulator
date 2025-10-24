from core.Landers.Lander import Lander
import numpy as np


class MoonLander(Lander):
    # Apollo 11 Lunar Module approximation
    def __init__(self, planet):
        dry = 15103 - 8200  # kg, dry mass = total - max fuel
        max_fuel = 8200     # kg
        thrust_per_engine = 45000.0  # N, one descent engine
        engine_count = 1
        dims = (8.2, 4.2, 6.4)  # m, width, height, depth - approx
        super().__init__(dry, max_fuel, thrust_per_engine, engine_count,
                         drag_coefficient=0.8, planet=planet, dimensions=dims)

        # single descent engine at center of vehicle bottom, pointing upward
        pos = np.array([0.0, -self.dimensions[1] / 2.0, 0.0])
        dirv = np.array([0.0, 1.0, 0.0])
        self.configure_engines([pos], [dirv])

    def get_name(self):
        return "Moon Lander"
