
# This class logs simulation data over time and provides simple plotting.

import matplotlib.pyplot as plt

class DataLogger:
    def __init__(self):
        self.times = []
        self.heights = []
        self.velocities = []

    def log(self, time, height, velocity):
        self.times.append(time)
        self.heights.append(height)
        self.velocities.append(velocity)

    def plot(self):
        plt.figure(figsize=(10, 5))
        plt.subplot(1, 2, 1)
        plt.plot(self.times, self.heights)
        plt.xlabel("Time [s]")
        plt.ylabel("Height [m]")
        plt.title("Height over Time")

        plt.subplot(1, 2, 2)
        plt.plot(self.times, self.velocities)
        plt.xlabel("Time [s]")
        plt.ylabel("Vertical Velocity [m/s]")
        plt.title("Vertical Velocity over Time")

        plt.tight_layout()
        plt.show()

        #sdaasdas