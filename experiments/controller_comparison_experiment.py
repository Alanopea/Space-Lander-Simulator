"""
Simple Controller Comparison Experiment

Purpose:
Compare PID, LQR, and MPC controllers under identical conditions
for a vertical velocity regulation landing problem.

All controllers:
- Same initial state
- Same physics
- Same actuator limits
- Same objective

Plots:
1) Vertical velocity vs time (+ ideal reference)
2) Altitude vs time
3) Throttle / control effort vs time
4) Cumulative fuel usage
"""

import numpy as np
import matplotlib.pyplot as plt
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.EnvironmentManager import EnvironmentManager
from core.Simulator import Simulator
from core.controllers.controller_factory import make_controller
from core.config import PID_DEFAULTS, LQR_DEFAULTS, MPC_DEFAULTS


class SimpleControllerExperiment:

    def __init__(self):
        self.env = EnvironmentManager()

        # ---------- INITIAL CONDITIONS ----------
        self.initial_altitude = 500.0        # m
        self.initial_velocity = -50.0        # m/s (downward)
        self.target_velocity = -3.0          # m/s at touchdown
        self.target_altitude = 0.0           # m

        self.dt = 0.05                       # s
        self.max_time = 300.0                # s

        self.accel_limits = (-9.81, 20.0) 

        # ---------- CONTROLLER CONFIGS ----------
        self.controller_configs = {
            "PID": {
                **PID_DEFAULTS,
                "kind": "pid",
                "setpoint": self.target_velocity,
                "output_limits": self.accel_limits,
                "activation_altitude": 0.0
            },
            "LQR": {
                **LQR_DEFAULTS,
                "kind": "lqr",
                "setpoint": self.target_velocity,
                "activation_altitude": 0.0
            },
            "MPC": {
                **MPC_DEFAULTS,
                "kind": "mpc",
                "setpoint": self.target_velocity,
                "output_limits": self.accel_limits,
                "dt_nom": self.dt,
                "activation_altitude": 0.0,
                "gravity": None
            }
        }

    # ============================================================
    # Reference trajectory (constant-acceleration braking)
    # ============================================================
    def generate_reference(self, planet):
        g = planet.gravity

        u = self.initial_velocity
        v = self.target_velocity
        s = self.initial_altitude

        a = (v**2 - u**2) / (2 * s)
        a = np.clip(a, self.accel_limits[0], self.accel_limits[1])

        t_final = (v - u) / a

        times = np.arange(0, t_final, self.dt)
        velocities = u + a * times
        altitudes = s + u * times + 0.5 * a * times**2
        altitudes = np.maximum(altitudes, 0.0)

        return times, velocities, altitudes

    # ============================================================
    # Single controller run
    # ============================================================
    def run_controller(self, planet_name, controller_name):
        planet = self.env.get_planet(planet_name)

        if controller_name == "MPC":
            self.controller_configs["MPC"]["gravity"] = planet.gravity

        controller = make_controller(**self.controller_configs[controller_name])

        sim = Simulator(
            planet=planet,
            controller=controller,
            initial_altitude=self.initial_altitude,
            initial_velocity=self.initial_velocity,
            lander_class=None
        )

        t = 0.0
        fuel_used = 0.0

        data = {
            "time": [],
            "altitude": [],
            "velocity": [],
            "throttle": [],
            "fuel": []
        }

        while t < self.max_time:
            sim.step(self.dt)
            tel = sim.get_telemetry()

            altitude = tel["position"][1]
            velocity = tel["velocity"][1]

            total_thrust = sum(e.current_thrust for e in sim.lander.engines)
            max_thrust = sim.lander.get_max_total_thrust()
            throttle = total_thrust / max_thrust if max_thrust > 0 else 0.0

            fuel_used += sim.lander.fuel_consumption_rate * self.dt

            data["time"].append(t)
            data["altitude"].append(altitude)
            data["velocity"].append(velocity)
            data["throttle"].append(throttle * 100.0)
            data["fuel"].append(fuel_used)

            t += self.dt

            if altitude <= 0.0:
                break

        return data

    # ============================================================
    # Plotting
    # ============================================================
    def plot(self, planet_name, results, reference):
        fig, axs = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(f"Controller Comparison – {planet_name}", fontsize=16)

        # --- Plot 1: Velocity ---
        ax = axs[0, 0]
        for name, data in results.items():
            ax.plot(data["time"], data["velocity"], label=name)
        #ax.plot(reference[0], reference[1], "k--", label="Ideal reference")
        ax.set_ylabel("Vertical velocity (m/s)")
        ax.set_xlabel("Time (s)")
        ax.set_title("Velocity vs Time")
        ax.legend()
        ax.grid(True)

        # --- Plot 2: Altitude ---
        ax = axs[0, 1]
        for name, data in results.items():
            ax.plot(data["time"], data["altitude"], label=name)
        #ax.plot(reference[0], reference[2], "k--", label="Ideal reference")
        ax.set_ylabel("Altitude (m)")
        ax.set_xlabel("Time (s)")
        ax.set_title("Altitude vs Time")
        ax.legend()
        ax.grid(True)

        # --- Plot 3: Throttle ---
        ax = axs[1, 0]
        for name, data in results.items():
            ax.plot(data["time"], data["throttle"], label=name)
        ax.set_ylabel("Throttle (%)")
        ax.set_xlabel("Time (s)")
        ax.set_title("Control Effort")
        ax.legend()
        ax.grid(True)

        # --- Plot 4: Fuel ---
        ax = axs[1, 1]
        for name, data in results.items():
            ax.plot(data["time"], data["fuel"], label=name)
        ax.set_ylabel("Fuel used (kg)")
        ax.set_xlabel("Time (s)")
        ax.set_title("Cumulative Fuel Usage")
        ax.legend()
        ax.grid(True)

        save_dir = "experiments/comparison_results"
        os.makedirs(save_dir, exist_ok=True)  # create save folder if it doesn't exist

        filename = f"controller_comparison_{planet_name.lower()}.png"
        filepath = os.path.join(save_dir, filename)

        plt.tight_layout()
        plt.savefig(filepath, dpi=300)
        plt.close(fig)


    # ============================================================
    # Run all
    # ============================================================
    def run(self):
        for planet_name in ["Earth", "Moon", "Mars"]:
            print(f"\nRunning experiment on {planet_name}")

            planet = self.env.get_planet(planet_name)
            reference = self.generate_reference(planet)

            results = {}
            for ctrl in ["PID", "LQR", "MPC"]:
                print(f"  Running {ctrl}")
                results[ctrl] = self.run_controller(planet_name, ctrl)

            self.plot(planet_name, results, reference)


if __name__ == "__main__":
    SimpleControllerExperiment().run()
