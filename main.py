
# Main entry point for the simulation. Selects planet and starts simulation.

from EnvironmentManager import EnvironmentManager
from Simulator import Simulator

if __name__ == "__main__":
    manager = EnvironmentManager()
    available_planets = manager.list_planets()
    print("Available planets:", available_planets)

    # Input validation loop
    while True:
        planet_name = input("Select planet: ").capitalize()
        if planet_name in available_planets:
            break
        else:
            print("Pick one from the available planets:", available_planets)

    planet = manager.get_planet(planet_name)
    simulator = Simulator(planet)

    # Run simulation with example thrust parameters
    simulator.run(thrust_angle=1.57, thrust_force=1500, duration=60, dt=0.1)