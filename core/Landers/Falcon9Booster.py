from core.Landers.Lander import Lander
import numpy as np

class Falcon9Booster(Lander):
    # Falcon 9 first stage approximation
    def __init__(self, planet):
        dry = 25600  # kg, dry mass = total - max fuel
        max_fuel = 395700  # kg
        thrust_per_engine = 845000.0  # N, one Merlin engine
        engine_count = 9
        dims = (3.7, 70.0, 3.7)  # m, width, height, depth - approx
        super().__init__(dry, max_fuel, thrust_per_engine, engine_count,
                         drag_coefficient=0.75, planet=planet, dimensions=dims)

        # Engine layout: center + 8 engines in a ring around the center
        # radius chosen inside the booster diameter
        radius = min(self.dimensions[0] / 2.0 * 0.9, 1.8)
        y_pos = -self.dimensions[1] / 2.0  # engines mounted at the bottom surface
        positions = []
        directions = []

        # center engine
        positions.append(np.array([0.0, y_pos, 0.0]))
        directions.append(np.array([0.0, 1.0, 0.0]))

        # 8 engines in a ring
        for i in range(8):
            theta = 2.0 * np.pi * i / 8.0
            x = radius * np.cos(theta)
            z = radius * np.sin(theta)
            positions.append(np.array([x, y_pos, z]))
            directions.append(np.array([0.0, 1.0, 0.0]))  # all point upward

        self.configure_engines(positions, directions)

    def get_name(self):
        return "Falcon 9 Booster"