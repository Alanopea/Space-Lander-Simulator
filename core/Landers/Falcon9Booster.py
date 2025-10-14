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
        super().__init__(dry, max_fuel, thrust_per_engine, engine_count, drag_coefficient=0.75, planet=planet, dimensions=dims)

    def get_name(self):
        return "Falcon 9 Booster"