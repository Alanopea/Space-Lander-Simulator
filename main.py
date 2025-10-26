# Main entry point for the simulation. Selects planet and starts simulation.

from core.EnvironmentManager import EnvironmentManager
from core.Simulator import Simulator
from core.config import make_default_controller, INITIAL_ALTITUDE

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
    
    # build controller from centralized config
    controller = make_default_controller()

    simulator = Simulator(planet, controller=controller, initial_altitude=INITIAL_ALTITUDE)
    simulator.run(duration=60, dt=0.1)