
# This class defines a planetary environment with specific gravity and atmospheric density.

class Planet:
    def __init__(self, name, gravity, air_density):
        self.name = name
        self.gravity = gravity
        self.air_density = air_density

# Predefined planets
earth = Planet(name="Earth", gravity=9.81, air_density=1.225)
mars = Planet(name="Mars", gravity=3.71, air_density=0.02)
moon = Planet(name="Moon", gravity=1.62, air_density=0)
        
