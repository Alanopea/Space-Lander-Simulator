from PyQt5.QtWidgets import QApplication
from UI.dashboard_UI import Dashboard
from UI.panels.simulation_controls_UI import SimulationControls
from core.EnvironmentManager import EnvironmentManager
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)

    env_mgr = EnvironmentManager()
    dashboard = Dashboard()

    # create controls as a child and embed into dashboard via connect_controls()
    controls = SimulationControls(env_mgr, parent=dashboard)
    dashboard.connect_controls(controls)

    dashboard.show()

    sys.exit(app.exec_())