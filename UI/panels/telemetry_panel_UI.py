from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
import pyqtgraph as pg

class TelemetryPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        self.status_label = QLabel("Status: Descending")
        self.altitude_label = QLabel("Altitude: 1000 m")
        self.velocity_label = QLabel("Velocity: -15 m/s")
        self.attitude_label = QLabel("Attitude: (0,0,0)")

        layout.addWidget(self.status_label)
        layout.addWidget(self.altitude_label)
        layout.addWidget(self.velocity_label)
        layout.addWidget(self.attitude_label)

        # Real-time plot
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setTitle("Altitude vs Time")
        self.plot_widget.setLabel("bottom", "Time", "s")
        self.plot_widget.setLabel("left", "Altitude", "m")
        self.altitude_curve = self.plot_widget.plot(pen="y")
        layout.addWidget(self.plot_widget)

        self.setLayout(layout)

        self.time_data = []
        self.altitude_data = []
