# This class defines a planetary environment with specific gravity and atmospheric density.

class Planet:
    def __init__(self, name, gravity, air_density, mass, radius, initial_altitude=None, initial_velocity=None):
        self.name = name
        self.gravity = float(gravity) # surface gravity (m/s^2)
        self.air_density = float(air_density)
        self.mass = float(mass)
        self.radius = float(radius)
        self.initial_altitude = float(initial_altitude) if initial_altitude is not None else None
        self.initial_velocity = float(initial_velocity) if initial_velocity is not None else None

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
    radius=6.371e6,
    initial_altitude=1500.0,
    initial_velocity=-130.0
)

# Mars
mars = Planet(
    name="Mars",
    gravity=3.71,
    air_density=0.02,
    mass=6.417e23,
    radius=3.3895e6,
    initial_altitude=2000.0,
    initial_velocity=-55.0
)

# Moon
moon = Planet(
    name="Moon",
    gravity=1.62,
    air_density=0,
    mass=7.342e22,
    radius=1.737e6,
    initial_altitude=1200.0,
    initial_velocity=-35.0
)