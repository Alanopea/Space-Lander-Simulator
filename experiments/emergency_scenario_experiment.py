"""
Emergency Scenario Impact Analysis Experiment

Plots Generated:
1) Landing Success/Failure Matrix
2) Impact Velocity Comparison
3) Fuel Consumption by Scenario
4) Velocity Profiles (comparison with nominal)
5) Altitude Profiles (descent trajectory)
6) Throttle Commands (control effort)
"""

import numpy as np
import matplotlib.pyplot as plt
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.EnvironmentManager import EnvironmentManager
from core.Simulator import Simulator
from core.Landers.Falcon9Booster import Falcon9Booster
from core.controllers.controller_factory import make_controller
from core.config import MPC_DEFAULTS


class EmergencyScenarioExperiment:

    def __init__(self):
        self.env = EnvironmentManager()

        # ---------- INITIAL CONDITIONS ----------
        self.initial_altitude = 500.0        # m
        self.initial_velocity = -70.0        # m/s (downward)
        self.target_velocity = -3.0          # m/s at touchdown (safe landing)
        self.crash_threshold = -5.0          # m/s - landing faster = crash

        self.dt = 0.05                       # s
        self.max_time = 300.0                # s (5 minutes for worst case scenarios)

        # ---------- ACTUATOR LIMITS ----------
        self.accel_limits = (-9.81, 20.0)    # m/s²

        # ---------- EMERGENCY SCENARIOS ----------
        # Key: scenario name, Value: emergency config
        self.scenarios = {
            "Nominal (No Emergency)": None,
            "One Engine Failure": {
                "type": "engine_failure",
                "params": {"count": 1}
            },
            "Two Engine Failures": {
                "type": "engine_failure",
                "params": {"count": 2}
            },
            "One Engine Stuck at 100%": {
                "type": "engine_stuck",
                "params": {"throttle": 1.0}
            },
            "Response Lag: Mild (0.1s)": {
                "type": "response_lag",
                "params": {"delay": 0.1}
            },
            "Response Lag: Medium (0.5s)": {
                "type": "response_lag",
                "params": {"delay": 0.5}
            },
            "Response Lag: Severe (1.0s)": {
                "type": "response_lag",
                "params": {"delay": 1.0}
            }
        }

    # ============================================================
    # Run single emergency scenario
    # ============================================================
    def run_scenario(self, scenario_name, emergency_config):
        """
        Run a single simulation with given emergency scenario.
        
        Returns dict with telemetry data and landing metrics.
        """
        planet = self.env.get_planet("Earth")
        
        # Configure MPC controller
        mpc_config = {
            **MPC_DEFAULTS,
            "kind": "mpc",
            "setpoint": self.target_velocity,
            "output_limits": self.accel_limits,
            "dt_nom": self.dt,
            "activation_altitude": 0.0,
            "gravity": planet.gravity
        }
        
        controller = make_controller(**mpc_config)
        
        # Create simulator with emergency scenario
        sim = Simulator(
            planet=planet,
            controller=controller,
            initial_altitude=self.initial_altitude,
            initial_velocity=self.initial_velocity,
            lander_class=Falcon9Booster,
            emergency_scenario_config=emergency_config
        )

        t = 0.0
        fuel_used = 0.0
        landed = False
        crashed = False

        data = {
            "time": [],
            "altitude": [],
            "velocity": [],
            "throttle": [],
            "fuel": [],
            "engine_thrust": []
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
            fuel_remaining = sim.lander.fuel_mass

            data["time"].append(t)
            data["altitude"].append(altitude)
            data["velocity"].append(velocity)
            data["throttle"].append(throttle * 100.0)
            data["fuel"].append(fuel_used)
            data["engine_thrust"].append(total_thrust)

            t += self.dt

            # Check landing condition
            if altitude <= 0.0:
                if velocity < self.crash_threshold:  # velocity more negative than -5 m/s
                    crashed = True
                else:
                    landed = True
                break
            
            # Check fuel depletion
            if fuel_remaining <= 0.0:
                crashed = True  # Emergency stop due to fuel
                break

        # Calculate metrics
        metrics = {
            "scenario": scenario_name,
            "landed": landed,
            "crashed": crashed,
            "impact_velocity": data["velocity"][-1] if data["velocity"] else 0.0,
            "fuel_used": fuel_used,
            "max_throttle": max(data["throttle"]) if data["throttle"] else 0.0,
            "avg_throttle": np.mean(data["throttle"]) if data["throttle"] else 0.0,
            "descent_time": t,
            "data": data
        }
        
        return metrics

    # ============================================================
    # Statistical Analysis
    # ============================================================
    def analyze_results(self, all_results):
        """
        Compute statistics across all scenarios.
        Returns summary dataframe.
        """
        summary = []
        for result in all_results:
            summary.append({
                "Scenario": result["scenario"],
                "Success": " LANDED" if result["landed"] else " CRASHED",
                "Impact Velocity (m/s)": f"{result['impact_velocity']:.2f}",
                "Fuel Used (kg)": f"{result['fuel_used']:.2f}",
                "Max Throttle (%)": f"{result['max_throttle']:.1f}",
                "Avg Throttle (%)": f"{result['avg_throttle']:.1f}",
                "Descent Time (s)": f"{result['descent_time']:.2f}"
            })
        
        return summary

    def _is_response_lag_scenario(self, scenario_name):
        """Check if a scenario is a response lag scenario."""
        return "Response Lag" in scenario_name

    # ============================================================
    # Plotting Functions
    # ============================================================
    def plot_landing_outcomes(self, all_results):
        """Plot 1: Landing success/failure summary"""
        scenarios = [r["scenario"] for r in all_results]
        success = [1 if r["landed"] else 0 for r in all_results]
        crash = [1 if r["crashed"] else 0 for r in all_results]

        fig, ax = plt.subplots(figsize=(12, 6))
        
        x_pos = np.arange(len(scenarios))
        width = 0.35

        bars1 = ax.bar(x_pos - width/2, success, width, label="Safe Landing", color="#2ecc71", alpha=0.8)
        bars2 = ax.bar(x_pos + width/2, crash, width, label="Crash", color="#e74c3c", alpha=0.8)

        ax.set_ylabel("Outcome (1 = Yes, 0 = No)", fontsize=12)
        ax.set_title("Emergency Scenario Impact: Landing Outcomes", fontsize=14, fontweight='bold')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(scenarios, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_ylim([0, 1.1])

        plt.tight_layout()
        save_dir = "experiments/emergencies_results"
        os.makedirs(save_dir, exist_ok=True)
        plt.savefig(os.path.join(save_dir, "emergency_01_landing_outcomes.png"), dpi=300)
        plt.close(fig)

    def plot_impact_velocity(self, all_results):
        """Plot 2: Impact velocity comparison"""
        scenarios = [r["scenario"] for r in all_results]
        impact_vels = [r["impact_velocity"] for r in all_results]
        
        # Color code: green if safe, red if crash
        colors = ["#2ecc71" if r["landed"] else "#e74c3c" for r in all_results]

        fig, ax = plt.subplots(figsize=(12, 6))
        
        bars = ax.bar(scenarios, impact_vels, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
        
        # Add threshold line
        ax.axhline(y=self.crash_threshold, color='red', linestyle='--', linewidth=2, label='Crash Threshold (-5 m/s)')
        ax.axhline(y=self.target_velocity, color='green', linestyle='--', linewidth=2, label='Target Velocity (-3 m/s)')

        ax.set_ylabel("Impact Velocity (m/s)", fontsize=12)
        ax.set_title("Emergency Scenario Impact: Landing Velocity\n(Negative = Downward)", fontsize=14, fontweight='bold')
        ax.set_xticklabels(scenarios, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar, vel in zip(bars, impact_vels):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{vel:.2f}', ha='center', va='bottom' if vel > self.crash_threshold else 'top', fontsize=9)

        plt.tight_layout()
        save_dir = "experiments/emergencies_results"
        os.makedirs(save_dir, exist_ok=True)
        plt.savefig(os.path.join(save_dir, "emergency_02_impact_velocity.png"), dpi=300)
        plt.close(fig)

    def plot_fuel_consumption(self, all_results):
        """Plot 3: Fuel consumption by scenario"""
        scenarios = [r["scenario"] for r in all_results]
        fuel_used = [r["fuel_used"] for r in all_results]
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        bars = ax.bar(scenarios, fuel_used, color="#3498db", alpha=0.8, edgecolor='black', linewidth=1.5)
        
        ax.set_ylabel("Fuel Consumed (kg)", fontsize=12)
        ax.set_title("Emergency Scenario Impact: Fuel Efficiency", fontsize=14, fontweight='bold')
        ax.set_xticklabels(scenarios, rotation=45, ha='right')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels
        for bar, fuel in zip(bars, fuel_used):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{fuel:.1f}', ha='center', va='bottom', fontsize=9)

        plt.tight_layout()
        save_dir = "experiments/emergencies_results"
        os.makedirs(save_dir, exist_ok=True)
        plt.savefig(os.path.join(save_dir, "emergency_03_fuel_consumption.png"), dpi=300)
        plt.close(fig)

    def plot_velocity_profiles(self, all_results):
        """Plot 4: Velocity vs time for all scenarios (excluding response lag)"""
        # Filter out response lag scenarios
        results = [r for r in all_results if not self._is_response_lag_scenario(r["scenario"])]
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        for i, result in enumerate(results):
            data = result["data"]
            outcome = "(S)" if result["landed"] else "(F)"
            label = f"{outcome} {result['scenario']}"
            
            # Line style: solid for nominal, dashed for failed
            linestyle = '-' if result["scenario"] == "Nominal (No Emergency)" else '--'
            linewidth = 2.5 if result["scenario"] == "Nominal (No Emergency)" else 1.5
            
            ax.plot(data["time"], data["velocity"], label=label, linestyle=linestyle, linewidth=linewidth)
        
        # Add crash threshold line
        ax.axhline(y=self.crash_threshold, color='red', linestyle=':', linewidth=2, alpha=0.7, label='Crash Threshold')
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5, alpha=0.5)
        
        ax.set_xlabel("Time (s)", fontsize=12)
        ax.set_ylabel("Vertical Velocity (m/s)", fontsize=12)
        ax.set_title("Emergency Scenario Impact: Velocity Profiles\n(Negative = Downward)", fontsize=14, fontweight='bold')
        ax.legend(loc='best', fontsize=9)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        save_dir = "experiments/emergencies_results"
        os.makedirs(save_dir, exist_ok=True)
        plt.savefig(os.path.join(save_dir, "emergency_04_velocity_profiles.png"), dpi=300)
        plt.close(fig)

    def plot_altitude_profiles(self, all_results):
        """Plot 5: Altitude vs time for all scenarios (excluding response lag)"""
        # Filter out response lag scenarios
        results = [r for r in all_results if not self._is_response_lag_scenario(r["scenario"])]
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        for result in results:
            data = result["data"]
            outcome = "(S)" if result["landed"] else "(F)"
            label = f"{outcome} {result['scenario']}"
            
            linestyle = '-' if result["scenario"] == "Nominal (No Emergency)" else '--'
            linewidth = 2.5 if result["scenario"] == "Nominal (No Emergency)" else 1.5
            
            ax.plot(data["time"], data["altitude"], label=label, linestyle=linestyle, linewidth=linewidth)
        
        ax.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.5, label='Ground Level')
        
        ax.set_xlabel("Time (s)", fontsize=12)
        ax.set_ylabel("Altitude (m)", fontsize=12)
        ax.set_title("Emergency Scenario Impact: Descent Trajectories", fontsize=14, fontweight='bold')
        ax.legend(loc='best', fontsize=9)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        save_dir = "experiments/emergencies_results"
        os.makedirs(save_dir, exist_ok=True)
        plt.savefig(os.path.join(save_dir, "emergency_05_altitude_profiles.png"), dpi=300)
        plt.close(fig)

    def plot_throttle_profiles(self, all_results):
        """Plot 6: Throttle (control effort) vs time (excluding response lag)"""
        # Filter out response lag scenarios
        results = [r for r in all_results if not self._is_response_lag_scenario(r["scenario"])]
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        for result in results:
            data = result["data"]
            outcome = "(S)" if result["landed"] else "(F)"
            label = f"{outcome} {result['scenario']}"
            
            linestyle = '-' if result["scenario"] == "Nominal (No Emergency)" else '--'
            linewidth = 2.5 if result["scenario"] == "Nominal (No Emergency)" else 1.5
            
            ax.plot(data["time"], data["throttle"], label=label, linestyle=linestyle, linewidth=linewidth)
        
        ax.axhline(y=100, color='red', linestyle=':', linewidth=1.5, alpha=0.5, label='Max Throttle')
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5, alpha=0.5)
        
        ax.set_xlabel("Time (s)", fontsize=12)
        ax.set_ylabel("Throttle (%)", fontsize=12)
        ax.set_title("Emergency Scenario Impact: Control Effort (Throttle Commands)", fontsize=14, fontweight='bold')
        ax.legend(loc='best', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_ylim([0, 110])
        
        plt.tight_layout()
        save_dir = "experiments/emergencies_results"
        os.makedirs(save_dir, exist_ok=True)
        plt.savefig(os.path.join(save_dir, "emergency_06_throttle_profiles.png"), dpi=300)
        plt.close(fig)

    def plot_velocity_profiles_lag(self, all_results):
        """Plot 7: Velocity vs time for response lag scenarios only (3 subplots)"""
        # Filter only response lag scenarios
        lag_results = [r for r in all_results if self._is_response_lag_scenario(r["scenario"])]
        
        # Sort by delay value
        lag_results.sort(key=lambda x: float(x["scenario"].split('(')[1].split('s')[0]))
        
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        
        for idx, result in enumerate(lag_results):
            ax = axes[idx]
            data = result["data"]
            outcome = "(S)" if result["landed"] else "(F)"
            label = f"{outcome} {result['scenario']}"
            
            ax.plot(data["time"], data["velocity"], label=label, linewidth=2.5, color='#2980b9')
            
            # Add crash threshold line
            ax.axhline(y=self.crash_threshold, color='red', linestyle=':', linewidth=2, alpha=0.7, label='Crash Threshold')
            ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5, alpha=0.5)
            
            ax.set_xlabel("Time (s)", fontsize=11)
            ax.set_ylabel("Vertical Velocity (m/s)", fontsize=11)
            ax.set_title(f"{result['scenario']}", fontsize=12, fontweight='bold')
            ax.legend(loc='best', fontsize=9)
            ax.grid(True, alpha=0.3)
        
        fig.suptitle("Response Lag Scenarios: Velocity Profiles Comparison\n(Negative = Downward)", 
                     fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()
        save_dir = "experiments/emergencies_results"
        os.makedirs(save_dir, exist_ok=True)
        plt.savefig(os.path.join(save_dir, "emergency_07_velocity_profiles_lag.png"), dpi=300, bbox_inches='tight')
        plt.close(fig)

    def plot_altitude_profiles_lag(self, all_results):
        """Plot 8: Altitude vs time for response lag scenarios only"""
        # Filter only response lag scenarios
        results = [r for r in all_results if self._is_response_lag_scenario(r["scenario"])]
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        for result in results:
            data = result["data"]
            outcome = "(S)" if result["landed"] else "(F)"
            label = f"{outcome} {result['scenario']}"
            
            ax.plot(data["time"], data["altitude"], label=label, linewidth=2)
        
        ax.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.5, label='Ground Level')
        
        ax.set_xlabel("Time (s)", fontsize=12)
        ax.set_ylabel("Altitude (m)", fontsize=12)
        ax.set_title("Response Lag Scenarios: Descent Trajectories", fontsize=14, fontweight='bold')
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        save_dir = "experiments/emergencies_results"
        os.makedirs(save_dir, exist_ok=True)
        plt.savefig(os.path.join(save_dir, "emergency_08_altitude_profiles_lag.png"), dpi=300)
        plt.close(fig)

    def plot_throttle_profiles_lag(self, all_results):
        """Plot 9: Throttle (control effort) vs time for response lag scenarios only (3 subplots)"""
        # Filter only response lag scenarios
        lag_results = [r for r in all_results if self._is_response_lag_scenario(r["scenario"])]
        
        # Sort by delay value
        lag_results.sort(key=lambda x: float(x["scenario"].split('(')[1].split('s')[0]))
        
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        
        for idx, result in enumerate(lag_results):
            ax = axes[idx]
            data = result["data"]
            outcome = "(S)" if result["landed"] else "(F)"
            label = f"{outcome} {result['scenario']}"
            
            ax.plot(data["time"], data["throttle"], label=label, linewidth=2.5, color='#2980b9')
            
            ax.axhline(y=100, color='red', linestyle=':', linewidth=1.5, alpha=0.5, label='Max Throttle')
            ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5, alpha=0.5)
            
            ax.set_xlabel("Time (s)", fontsize=11)
            ax.set_ylabel("Throttle (%)", fontsize=11)
            ax.set_title(f"{result['scenario']}", fontsize=12, fontweight='bold')
            ax.legend(loc='upper right', fontsize=9)
            ax.grid(True, alpha=0.3)
            ax.set_ylim([0, 110])
        
        fig.suptitle("Response Lag Scenarios: Control Effort Comparison (Throttle Commands)", 
                     fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()
        save_dir = "experiments/emergencies_results"
        os.makedirs(save_dir, exist_ok=True)
        plt.savefig(os.path.join(save_dir, "emergency_09_throttle_profiles_lag.png"), dpi=300, bbox_inches='tight')
        plt.close(fig)

    # ============================================================
    # Run All
    # ============================================================
    def run(self):
        print("=" * 70)
        print("EMERGENCY SCENARIO IMPACT ANALYSIS EXPERIMENT")
        print("=" * 70)
        print(f"Platform: Falcon 9 | Planet: Earth | Controller: MPC")
        print(f"Initial Altitude: {self.initial_altitude} m | Initial Velocity: {self.initial_velocity} m/s")
        print()

        all_results = []

        for scenario_name, emergency_config in self.scenarios.items():
            print(f"Running scenario: {scenario_name}...", end=" ")
            try:
                result = self.run_scenario(scenario_name, emergency_config)
                all_results.append(result)
                
                outcome = " LANDED" if result["landed"] else " CRASHED"
                print(f"{outcome} | Impact: {result['impact_velocity']:.2f} m/s | Fuel: {result['fuel_used']:.2f} kg")
            except Exception as e:
                print(f"FAILED: {e}")

        print("\n" + "=" * 70)
        print("RESULTS SUMMARY")
        print("=" * 70)
        
        summary = self.analyze_results(all_results)
        for row in summary:
            print(f"{row['Scenario']:40} | {row['Success']:15} | V={row['Impact Velocity (m/s)']:>6} | Fuel={row['Fuel Used (kg)']:>6} | Time={row['Descent Time (s)']:>7}")

        print("\n" + "=" * 70)
        print("GENERATING PLOTS...")
        print("=" * 70)

        self.plot_landing_outcomes(all_results)
        print(" Plot 1: Landing Outcomes")
        
        self.plot_impact_velocity(all_results)
        print(" Plot 2: Impact Velocity")
        
        self.plot_fuel_consumption(all_results)
        print(" Plot 3: Fuel Consumption")
        
        self.plot_velocity_profiles(all_results)
        print(" Plot 4: Velocity Profiles")
        
        self.plot_altitude_profiles(all_results)
        print(" Plot 5: Altitude Profiles")
        
        self.plot_throttle_profiles(all_results)
        print(" Plot 6: Throttle Profiles")
        
        self.plot_velocity_profiles_lag(all_results)
        print(" Plot 7: Response Lag - Velocity Profiles")
        
        self.plot_altitude_profiles_lag(all_results)
        print(" Plot 8: Response Lag - Altitude Profiles")
        
        self.plot_throttle_profiles_lag(all_results)
        print(" Plot 9: Response Lag - Throttle Profiles")

        print("\n" + "=" * 70)
        print("EXPERIMENT COMPLETE!")
        print("Results saved to: experiments/emergencies_results/")
        print("=" * 70)


if __name__ == "__main__":
    EmergencyScenarioExperiment().run()
