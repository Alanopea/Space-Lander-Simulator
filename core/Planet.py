# This class defines a planetary environment with specific gravity and atmospheric density.

class Planet:
    def __init__(self, name, gravity, air_density, mass, radius):
        self.name = name
        self.gravity = float(gravity) # surface gravity (m/s^2)
        self.air_density = float(air_density)
        self.mass = float(mass)
        self.radius = float(radius)

    def gravity_at_height(self, height):
        """
        Simple inverse-square gravity variation with altitude:
        g(h) = g0 * (R / (R + h))^2
        height in meters above surface.
        """
        if height is None:
            return self.gravity
        h = max(0.0, float(height))
        return self.gravity * (self.radius / (self.radius + h))**2


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