import numpy as np
from core.Landers.Lander import Lander
from core.PhysicsEngine import PhysicsEngine
from core.DataLogger import DataLogger
from core.ThrustAllocator import ThrustAllocator

class Simulator:
    def __init__(self, planet, controller=None, initial_altitude=1000.0, lander_class=None, lander_instance=None):
        self.planet = planet
        self.controller = controller

        # Determine lander to use
        if lander_instance is not None:
            self.lander = lander_instance
        else:
            if lander_class is None:
                from core.Landers.Falcon9Booster import Falcon9Booster
                lander_class = Falcon9Booster
            self.lander = lander_class(planet)

        # place at initial altitude
        self.lander.position = np.array([0.0, initial_altitude, 0.0])
        self.physics = PhysicsEngine(self.lander)
        self.logger = DataLogger()

        # thrust allocator instance (built from current lander engines)
        self.thrust_allocator = ThrustAllocator(self.lander.engines)

    def step(self, dt, thrust_vector=np.array([0.0, 1.0, 0.0]), thrust_force=None):
        gravity_fn = getattr(self.planet, "gravity_at_height", None)
        g = gravity_fn(self.lander.position[1]) if callable(gravity_fn) else getattr(self.planet, "gravity", 9.81)

        # If controller provided, interpret its output as desired vertical accel (m/s^2)
        if self.controller is not None:
            vertical_velocity = float(self.lander.velocity[1])
            desired_accel = float(self.controller.update(vertical_velocity, dt))
            # desired total thrust magnitude
            total_required = self.lander.mass * (desired_accel + g)
            # Build desired force vector (assume thrust_vector is the desired global force direction)
            desired_force_vec = np.asarray(thrust_vector, dtype=float)
            desired_force_vec = desired_force_vec / (np.linalg.norm(desired_force_vec) + 1e-12)
            desired_force_vec = desired_force_vec * total_required
            # For now we desire zero torque (centralized controller). Torque can be passed in future.
            desired_torque = np.zeros(3, dtype=float)

            # Allocate per-engine thrust magnitudes (N)
            applied_thrusts = self.thrust_allocator.allocate(desired_force_vec, desired_torque)

            # set engine throttles
            for i, e in enumerate(self.lander.engines):
                max_t = e.max_thrust if e.enabled else 0.0
                if max_t > 0:
                    e.throttle = float(applied_thrusts[i] / max_t)
                else:
                    e.throttle = 0.0

            thrust_force = float(np.sum(applied_thrusts))
        else:
            # user-provided scalar thrust_force or vector magnitude
            thrust_force = float(thrust_force) if thrust_force is not None else 0.0
            # distribute equally as fallback
            thrust_force = min(thrust_force, self.lander.get_max_total_thrust())
            self.lander.allocate_thrust_equal(thrust_force)

        # fuel consumption using applied thrust
        total_thrust_to_apply = thrust_force
        g0 = 9.80665
        isp = float(getattr(self.lander, "specific_impulse", 300.0))
        if total_thrust_to_apply > 0.0 and isp > 0.0:
            mass_flow = total_thrust_to_apply / (isp * g0)
            fuel_needed = mass_flow * dt
            if self.lander.fuel_mass <= 0.0:
                # no fuel -> zero throttles
                self.lander.set_all_throttles(0.0)
                total_thrust_to_apply = 0.0
            elif fuel_needed > self.lander.fuel_mass:
                # scale throttles proportionally and consume remaining fuel
                scale = self.lander.fuel_mass / fuel_needed
                for e in self.lander.engines:
                    e.throttle *= scale
                total_thrust_to_apply = sum(e.current_thrust for e in self.lander.engines)
                self.lander.consume_fuel(self.lander.fuel_mass)
            else:
                self.lander.consume_fuel(fuel_needed)

        # send to physics
        # assume thrust_vector describes direction; PhysicsEngine expects thrust_vector * thrust_force
        self.physics.update(thrust_vector, total_thrust_to_apply, dt)
        self.logger.log(None, self.lander.position, self.lander.velocity)

    def get_telemetry(self):
        return {
            'position': self.lander.position.copy(),
            'velocity': self.lander.velocity.copy(),
            'orientation': self.lander.orientation.copy(),
            'extras': self.lander.telemetry_extras()
        }

    def reset(self, initial_altitude=1000.0):
        self.lander.position = np.array([0.0, initial_altitude, 0.0])
        self.lander.velocity = np.array([0.0, 0.0, 0.0])
        self.lander.orientation = np.array([0.0, 0.0, 0.0])
        self.lander.angular_velocity = np.array([0.0, 0.0, 0.0])
        self.logger = DataLogger()
        # rebuild allocator in case engine config changed
        self.thrust_allocator = ThrustAllocator(self.lander.engines)

    def get_logger(self):
        return self.logger