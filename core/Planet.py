
# This class defines a planetary environment with specific gravity and atmospheric density.

class Planet:
    def __init__(self, name, gravity, air_density, mass, radius):
        self.name = name
        self.gravity = gravity # surface gravity for reference
        self.air_density = air_density
        self.mass = mass
        self.radius = radius

    def gravity_at_height(self, height):
        G = 6.67430e-11
        return G * self.mass / (self.radius + height)**2

# === PLANETS ===

# Earth
earth = Planet(
    name="Earth",
    gravity=9.81,
    air_density=1.225,
    mass=5.972e24,
    radius=6.371e6
)

# Mars
mars = Planet(
    name="Mars",
    gravity=3.71,
    air_density=0.02,
    mass=6.417e23,
    radius=3.3895e6
)

# Moon
moon = Planet(
    name="Moon",
    gravity=1.62,
    air_density=0,
    mass=7.342e22,
    radius=1.737e6
)