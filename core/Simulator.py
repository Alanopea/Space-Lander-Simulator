import numpy as np
from core.Landers.Lander import Lander
from core.PhysicsEngine import PhysicsEngine
from core.DataLogger import DataLogger
from core.ThrustManager import ThrustManager
from core.FuelManager import FuelManager
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

        # Managers for separation of concerns
        self.thrust_manager = ThrustManager(self.lander)
        self.fuel_manager = FuelManager(self.lander)

    def step(self, dt, thrust_vector=np.array([0.0, 1.0, 0.0]), thrust_force=None):
        """
        Advance simulation by one time step.
        
        Args:
            dt: Time step (s)
            thrust_vector: Desired thrust direction (used with controller)
            thrust_force: Manual thrust force (N) - only used if no controller
        """
        g = self._get_gravity()
        
        # Allocate thrust (controller-based or manual)
        if self.controller is not None:
            applied_thrusts = self._allocate_thrust_from_controller(dt, g, thrust_vector)
        else:
            applied_thrusts = self.thrust_manager.allocate_manual(thrust_force)
        
        # Apply fuel constraints and consume fuel
        applied_thrusts = self.fuel_manager.consume_fuel_for_thrusts(applied_thrusts, dt)
        total_thrust = float(np.sum(applied_thrusts))
        
        # Update physics
        self.physics.update(thrust_vector, total_thrust, dt)
        self.logger.log(None, self.lander.position, self.lander.velocity)
    
    def _get_gravity(self) -> float:
        """Get current gravity at lander altitude."""
        gravity_fn = getattr(self.planet, "gravity_at_height", None)
        if callable(gravity_fn):
            return gravity_fn(self.lander.position[1])
        return getattr(self.planet, "gravity", 9.81)
    
    def _allocate_thrust_from_controller(self, dt: float, gravity: float,
                                         thrust_vector: np.ndarray) -> np.ndarray:
        """Allocate thrust based on controller output."""
        vertical_velocity = float(self.lander.velocity[1])
        altitude = float(self.lander.position[1])
        desired_accel = float(self.controller.update(vertical_velocity, dt, altitude))
        return self.thrust_manager.allocate_from_controller(desired_accel, gravity, thrust_vector)

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
        self.lander.reset_fuel()  # Reset fuel to full
        self.logger = DataLogger()
        # Refresh managers in case engine config changed
        self.thrust_manager.refresh_allocator()
        if self.controller is not None:
            self.controller.reset()

    def get_logger(self):
        return self.logger
    
    def run(self, duration: float, dt: float):
        """
        Run simulation for specified duration.
        
        Args:
            duration: Total simulation time (s)
            dt: Time step (s)
        """
        time = 0.0
        while time < duration:
            self.step(dt)
            time += dt
            # Stop if landed
            if self.lander.position[1] <= 0.0:
                break