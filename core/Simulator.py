import numpy as np
from core.Landers.Lander import Lander
from core.PhysicsEngine import PhysicsEngine
from core.DataLogger import DataLogger
import matplotlib.pyplot as plt

class Simulator:
    def __init__(self, planet, controller=None, initial_altitude=1000.0, lander_class=None, lander_instance=None):
        """
        Simulator now accepts either:
          - lander_instance: a constructed Lander object, or
          - lander_class: a Lander subclass (callable taking planet)
        If neither provided, default to MoonLander.
        """
        self.planet = planet
        self.controller = controller

        # Determine lander to use
        if lander_instance is not None:
            self.lander = lander_instance
        else:
            if lander_class is None:
                # default lander
                from core.Landers.MoonLander import MoonLander
                lander_class = MoonLander
            self.lander = lander_class(planet)

        # place at initial altitude
        self.lander.position = np.array([0.0, initial_altitude, 0.0])
        self.physics = PhysicsEngine(self.lander)
        self.logger = DataLogger()

    def step(self, dt, thrust_vector=np.array([0.0, 1.0, 0.0]), thrust_force=None):
        """
        Advance the physical model by dt.
        - If a controller is provided, its output is interpreted as desired vertical acceleration (m/s^2).
        - That acceleration is converted to thrust force: F = m * (a_desired + g)
        - Thrust is clamped to [0, available_thrust], and fuel consumption is applied.
        """
        # determine gravity at current altitude (fallback to planet.gravity)
        gravity_fn = getattr(self.planet, "gravity_at_height", None)
        g = gravity_fn(self.lander.position[1]) if callable(gravity_fn) else getattr(self.planet, "gravity", 9.81)

        # Controller path: controller returns desired acceleration (m/s^2)
        if self.controller is not None:
            vertical_velocity = float(self.lander.velocity[1])
            desired_accel = float(self.controller.update(vertical_velocity, dt))
            # required thrust to produce desired_accel upward (positive up):
            required_thrust = self.lander.mass * (desired_accel + g)
            # clamp to physical engine capability
            max_thrust = float(getattr(self.lander, "get_total_thrust")())
            thrust_force = max(0.0, min(required_thrust, max_thrust))
        else:
            # user-provided thrust_force branch (assume it's N)
            thrust_force = float(thrust_force) if thrust_force is not None else 0.0

        # Simple fuel consumption model: mass_flow = thrust / (Isp * g0)
        # use lander.specific_impulse if present, else default 300 s
        g0 = 9.80665
        isp = float(getattr(self.lander, "specific_impulse", 300.0))
        if thrust_force > 0.0 and isp > 0.0:
            mass_flow = thrust_force / (isp * g0)  # kg/s
            fuel_needed = mass_flow * dt
            if self.lander.fuel_mass <= 0.0:
                # no fuel -> zero thrust
                thrust_force = 0.0
            elif fuel_needed > self.lander.fuel_mass:
                # not enough fuel to sustain required thrust for whole dt:
                # scale thrust proportionally to available fuel and consume it
                scale = self.lander.fuel_mass / fuel_needed
                thrust_force *= scale
                self.lander.consume_fuel(self.lander.fuel_mass)
            else:
                self.lander.consume_fuel(fuel_needed)

        # send to physics
        self.physics.update(thrust_vector, thrust_force, dt)
        self.logger.log(None, self.lander.position, self.lander.velocity)

    def get_telemetry(self):
        return {
            'position': self.lander.position.copy(),
            'velocity': self.lander.velocity.copy(),
            'orientation': self.lander.orientation.copy()
        }

    def reset(self, initial_altitude=1000.0):
        self.lander.position = np.array([0.0, initial_altitude, 0.0])
        self.lander.velocity = np.array([0.0, 0.0, 0.0])
        self.lander.orientation = np.array([0.0, 0.0, 0.0])
        self.lander.angular_velocity = np.array([0.0, 0.0, 0.0])
        self.logger = DataLogger()

    def run(self, thrust_vector=np.array([0.0, 1.0, 0.0]), thrust_force=300, duration=60, dt=0.1):
        time = 0.0
        while time < duration and self.lander.position[1] > 0:
            if self.controller:
                vertical_velocity = self.lander.velocity[1]
                # controller returns desired accel -> step() will convert to thrust and apply fuel consumption
                self.step(dt, thrust_vector=thrust_vector)
                # logger and prints are handled below by the step call
                time += dt
                # continue to next loop since step already did update & logging
                print(f"Time: {time:.1f}s | Pos: {self.lander.position} | Vel: {self.lander.velocity} | Ori: {self.lander.orientation}")
                continue
            else:
                self.physics.update(thrust_vector, thrust_force, dt)
            self.logger.log(time, self.lander.position, self.lander.velocity)
            print(f"Time: {time:.1f}s | Pos: {self.lander.position} | Vel: {self.lander.velocity} | Ori: {self.lander.orientation}")
            print(f"Thrust applied: {thrust_force:.2f} N | Fuel remaining: {self.lander.fuel_mass:.2f} kg")
            time += dt
        self.logger.plot()

    def get_logger(self):
        return self.logger