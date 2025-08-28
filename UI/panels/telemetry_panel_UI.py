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

    def update_telemetry(self, time, altitude, velocity, attitude, status=None):
        """Update labels and plot with new data"""
        self.altitude_label.setText(f"Altitude: {altitude:.1f} m")
        self.velocity_label.setText(f"Velocity: {velocity:.1f} m/s")
        self.attitude_label.setText(f"Attitude: {attitude}")

        if status:
            self.status_label.setText(f"Status: {status}")

        # update plot
        self.time_data.append(time)
        self.altitude_data.append(altitude)
        self.altitude_curve.setData(self.time_data, self.altitude_data)