# Main entry point for the simulation. Selects planet and starts simulation.

from core.EnvironmentManager import EnvironmentManager
from core.Simulator import Simulator
from core.controllers.pid_controller import PIDController

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
    
    # Setpoint: target descent rate at touchdown
    pid = PIDController(kp=300, ki=0, kd=120, setpoint=-2.0, output_limits=(0.0, 2.0e6))

    simulator = Simulator(planet, controller=pid)
    simulator.run(duration=60, dt=0.1)