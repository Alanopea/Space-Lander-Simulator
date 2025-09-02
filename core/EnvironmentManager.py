
# This class manages available planets and allows switching between them.

from core.Planet import earth, mars, moon

class EnvironmentManager:
    def __init__(self):
        self.planets = {
            "Earth": earth,
            "Mars": mars,
            "Moon": moon
        }

    def get_planet(self, name):
        return self.planets.get(name, mars)

    def list_planets(self):
        return list(self.planets.keys())