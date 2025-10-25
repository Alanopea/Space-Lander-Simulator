import numpy as np
from core.Landers.Lander import Lander

class StarshipPayload(Lander):
    """
    Starship second stage (approximation).
    - Uses planet.name to pick engine types:
      * Moon -> only inner vacuum Raptors (3)
      * Earth/Mars -> only outer sea-level Raptors (3)
      * otherwise -> mixed (inner vacuum + outer sea-level, total 6)
    - Per-engine attributes engine_type and specific_impulse are attached to Engine instances.
    """
    def __init__(self, planet):
        # approximate masses (kg)
        dry = 12000.0        # dry mass (approx, payload + structure)
        max_fuel = 120000.0  # propellant mass (approx)

        # dimensions (width, height, depth) in meters (approx)
        dims = (9.0, 50.0, 9.0)

        # default per-engine thrust (fallback)
        thrust_per_engine = 2300000.0
        engine_count = 6

        super().__init__(dry, max_fuel, thrust_per_engine, engine_count,
                         drag_coefficient=0.5, planet=planet, dimensions=dims)

        # Approximate Raptor numbers (N and s)
        raptor_sea_level_thrust = 2300000.0   # N
        raptor_vacuum_thrust   = 2000000.0    # N
        isp_sea = 330.0    # s
        isp_vac = 380.0    # s

        # Determine planet name robustly (use Planet.name values you provided)
        try:
            if hasattr(planet, "name"):
                pname = str(planet.name).strip().lower()
            elif hasattr(planet, "get_name"):
                pname = str(planet.get_name()).strip().lower()
            else:
                pname = str(planet).strip().lower()
        except Exception:
            pname = ""

        # Use only vacuum on Moon, only sea-level on Earth/Mars, otherwise mixed
        use_all_vacuum = (pname == "moon")
        use_all_sea = (pname == "earth" or pname == "mars")

        # engine mount positions (inner triangle + outer ring)
        y_pos = -self.dimensions[1] / 2.0  # engines at bottom surface
        positions = []
        directions = []
        max_thrusts = []

        inner_radius = 0.6
        outer_radius = min(self.dimensions[0] / 2.0 * 0.9, 3.5)

        def add_engine(x, z, thrust):
            positions.append(np.array([x, y_pos, z]))
            directions.append(np.array([0.0, 1.0, 0.0]))
            max_thrusts.append(thrust)

        if use_all_vacuum:
            # only inner vacuum cluster (3 vacuum engines)
            for i in range(3):
                theta = 2.0 * np.pi * i / 3.0
                x = inner_radius * np.cos(theta)
                z = inner_radius * np.sin(theta)
                add_engine(x, z, raptor_vacuum_thrust)

        elif use_all_sea:
            # only outer sea-level ring (3 sea-level engines)
            for i in range(3):
                theta = 2.0 * np.pi * i / 3.0 + (np.pi / 3.0)
                x = outer_radius * np.cos(theta)
                z = outer_radius * np.sin(theta)
                add_engine(x, z, raptor_sea_level_thrust)

        else:
            # mixed layout: inner vacuum (3) + outer sea-level (3)
            for i in range(3):
                theta = 2.0 * np.pi * i / 3.0
                x = inner_radius * np.cos(theta)
                z = inner_radius * np.sin(theta)
                add_engine(x, z, raptor_vacuum_thrust)
            for i in range(3):
                theta = 2.0 * np.pi * i / 3.0 + (np.pi / 3.0)
                x = outer_radius * np.cos(theta)
                z = outer_radius * np.sin(theta)
                add_engine(x, z, raptor_sea_level_thrust)

        # configure engines on the Lander (uses existing API)
        self.configure_engines(positions, directions, max_thrusts)

        # annotate each Engine instance with engine_type and specific_impulse
        for e in self.engines:
            mt = float(getattr(e, "max_thrust", 0.0))
            # pick closest thrust to decide type
            if abs(mt - raptor_vacuum_thrust) <= abs(mt - raptor_sea_level_thrust):
                e.engine_type = "vacuum"
                e.specific_impulse = isp_vac
            else:
                e.engine_type = "sea_level"
                e.specific_impulse = isp_sea

    def get_name(self):
        return "Starship (Second Stage)"