
# This class holds the current state of the lander: mass, fuel, position, and velocity.

class Lander:
    def __init__(self, mass, fuel_mass, thrust_power, drag_coefficient, planet):
        self.mass = mass
        self.fuel_mass = fuel_mass
        self.thrust_power = thrust_power
        self.drag_coefficient = drag_coefficient
        self.planet = planet

        # Initial state
        self.position = [0.0, 1000.0]  # Starting 1000 meters above surface
        self.velocity = [0.0, 0.0]     # vx, vy