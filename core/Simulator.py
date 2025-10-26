import numpy as np
from core.Landers.Lander import Lander
from core.PhysicsEngine import PhysicsEngine
from core.DataLogger import DataLogger
from core.ThrustAllocator import ThrustAllocator
from core.config import make_default_controller

class Simulator:
    def __init__(self, planet, controller=None, initial_altitude=1000.0, initial_velocity=0.0, lander_class=None, lander_instance=None):
        self.planet = planet

        # If no controller provided, build default via factory (default = LQR)
        if controller is None:
            controller = make_default_controller()
        self.controller = controller

        # preserve starting velocity for reset
        self.initial_velocity = float(initial_velocity)

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
        # set initial vertical velocity (y axis)
        self.lander.velocity = np.array([0.0, self.initial_velocity, 0.0])
        self.physics = PhysicsEngine(self.lander)
        self.logger = DataLogger()

        # thrust allocator instance (built from current lander engines)
        self.thrust_allocator = ThrustAllocator(self.lander.engines)

    def step(self, dt, thrust_vector=np.array([0.0, 1.0, 0.0]), thrust_force=None):
        gravity_fn = getattr(self.planet, "gravity_at_height", None)
        g = gravity_fn(self.lander.position[1]) if callable(gravity_fn) else getattr(self.planet, "gravity", 9.81)

        applied_thrusts = None

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
            desired_torque = np.zeros(3, dtype=float)

            # Allocate per-engine thrust magnitudes (N)
            applied_thrusts = self.thrust_allocator.allocate(desired_force_vec, desired_torque)

            # set engine throttles according to allocated thrusts
            for i, e in enumerate(self.lander.engines):
                max_t = float(getattr(e, "max_thrust", 0.0)) if getattr(e, "enabled", True) else 0.0
                if max_t > 0.0:
                    e.throttle = float(applied_thrusts[i] / max_t)
                else:
                    e.throttle = 0.0

            thrust_force = float(np.sum(applied_thrusts))

        else:
            # user-provided scalar thrust_force or vector magnitude
            thrust_force = float(thrust_force) if thrust_force is not None else 0.0
            # clamp to max available
            thrust_force = min(thrust_force, self.lander.get_max_total_thrust())

            # distribute equally among enabled engines
            enabled_engines = [e for e in self.lander.engines if getattr(e, "enabled", True)]
            n_enabled = len(enabled_engines)
            if n_enabled > 0 and thrust_force > 0.0:
                per_engine = thrust_force / n_enabled
                applied_thrusts = np.zeros(len(self.lander.engines), dtype=float)
                for i, e in enumerate(self.lander.engines):
                    if getattr(e, "enabled", True):
                        applied_thrusts[i] = per_engine
                        e.throttle = per_engine / float(getattr(e, "max_thrust", per_engine))
                    else:
                        applied_thrusts[i] = 0.0
                        e.throttle = 0.0
            else:
                applied_thrusts = np.zeros(len(self.lander.engines), dtype=float)
                for e in self.lander.engines:
                    e.throttle = 0.0

        # Fuel consumption using applied thrust and per-engine specific impulse
        total_thrust_to_apply = float(np.sum(applied_thrusts)) if applied_thrusts is not None else 0.0
        g0 = 9.80665

        # compute mass flow using per-engine Isp if available
        mass_flow = 0.0
        for i, thrust_i in enumerate(applied_thrusts):
            if thrust_i <= 0.0:
                continue
            e = self.lander.engines[i]
            isp_i = float(getattr(e, "specific_impulse", getattr(self.lander, "specific_impulse", 300.0)))
            if isp_i > 0.0:
                mass_flow += thrust_i / (isp_i * g0)

        if mass_flow > 0.0:
            fuel_needed = mass_flow * dt
            if self.lander.fuel_mass <= 0.0:
                # no fuel -> zero throttles and no thrust
                for e in self.lander.engines:
                    e.throttle = 0.0
                total_thrust_to_apply = 0.0
                applied_thrusts = np.zeros_like(applied_thrusts)
            elif fuel_needed > self.lander.fuel_mass:
                # scale down applied thrusts proportionally to remaining fuel
                scale = self.lander.fuel_mass / fuel_needed
                for i, e in enumerate(self.lander.engines):
                    applied_thrusts[i] *= scale
                    max_t = float(getattr(e, "max_thrust", 0.0))
                    e.throttle = (applied_thrusts[i] / max_t) if max_t > 0 else 0.0
                total_thrust_to_apply = float(np.sum(applied_thrusts))
                # consume all remaining fuel
                self.lander.consume_fuel(self.lander.fuel_mass)
            else:
                # enough fuel, consume fuel_needed
                self.lander.consume_fuel(fuel_needed)
        else:
            fuel_needed = 0.0

        # send to physics
        # PhysicsEngine expects thrust_vector * thrust_force (direction + magnitude)
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
        self.lander.velocity = np.array([0.0, self.initial_velocity, 0.0])
        self.lander.orientation = np.array([0.0, 0.0, 0.0])
        self.lander.angular_velocity = np.array([0.0, 0.0, 0.0])
        self.logger = DataLogger()
        # rebuild allocator in case engine config changed
        self.thrust_allocator = ThrustAllocator(self.lander.engines)

    def get_logger(self):
        return self.logger