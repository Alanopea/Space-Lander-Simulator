
# This class manages available planets and allows switching between them.

from Planet import earth, mars, moon

class EnvironmentManager:
    def __init__(self):
        self.planets = {
            "Earth": earth,
            "Mars": mars,
            "Moon": moon
        }

    def list_planets(self):
        return list(self.planets.keys())