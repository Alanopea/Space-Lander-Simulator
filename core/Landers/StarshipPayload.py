from core.Landers.Lander import Lander
import numpy as np

class StarshipPayload(Lander):
    # SpaceX Starship upper stage / payload section (approximation).
    def __init__(self, planet):
        dry = 12000  # kg, dry mass = total - max fuel
        max_fuel = 0  # kg, no fuel in payload bay
        thrust_per_engine = 0.0  # N, no engines
        engine_count = 0
        dims = (9.0, 13.0, 9.0)  # m, width, height, depth - approx
        super().__init__(dry, max_fuel, thrust_per_engine, engine_count,
                         drag_coefficient=0.5, planet=planet, dimensions=dims)

        # Payload has no engines - ensure engines list is empty
        self.configure_engines([], [])
    
    def get_name(self):
        return "Starship Payload Bay"