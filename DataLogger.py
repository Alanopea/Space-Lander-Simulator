
# This class logs 3D simulation data and visualizes key metrics over time.

import matplotlib.pyplot as plt
import numpy as np

class DataLogger:
    def __init__(self):
        self.times = []
        self.positions = []
        self.velocities = []

    def log(self, time, position, velocity):
        self.times.append(time)
        self.positions.append(position.copy())
        self.velocities.append(velocity.copy())

    def plot(self):
        pos_array = np.array(self.positions)
        vel_array = np.array(self.velocities)

        plt.figure(figsize=(12, 6))
        plt.subplot(1, 2, 1)
        plt.plot(self.times, pos_array[:, 1])  # Y (altitude)
        plt.xlabel("Time [s]")
        plt.ylabel("Altitude [m]")
        plt.title("Altitude over Time")

        plt.subplot(1, 2, 2)
        plt.plot(self.times, vel_array[:, 1])  # Y velocity
        plt.xlabel("Time [s]")
        plt.ylabel("Vertical Velocity [m/s]")
        plt.title("Vertical Velocity over Time")

        plt.tight_layout()
        plt.show()