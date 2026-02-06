# This class manages available landers and their planet compatibility.

from core.Landers.MoonLander import MoonLander
from core.Landers.Falcon9Booster import Falcon9Booster


class LanderManager:
    def __init__(self):
        # Map lander names to their classes and compatible planets
        self.landers = {
            "Moon Lander": {
                "class": MoonLander,
                "compatible_planets": ["Moon"]
            },
            "Falcon 9 Booster": {
                "class": Falcon9Booster,
                "compatible_planets": ["Mars", "Earth"]
            }
        }

    def get_lander_class(self, name):
        """Get the lander class for a given name."""
        lander_info = self.landers.get(name)
        if lander_info:
            return lander_info["class"]
        return None

    def list_landers(self):
        """Get list of all available lander names."""
        return list(self.landers.keys())

    def get_compatible_landers(self, planet_name):
        """Get list of lander names compatible with a given planet."""
        compatible = []
        for name, info in self.landers.items():
            if planet_name in info["compatible_planets"]:
                compatible.append(name)
        return compatible

    def is_compatible(self, lander_name, planet_name):
        """Check if a lander is compatible with a planet."""
        lander_info = self.landers.get(lander_name)
        if lander_info:
            return planet_name in lander_info["compatible_planets"]
        return False

