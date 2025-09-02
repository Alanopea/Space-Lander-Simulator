from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
import pyqtgraph as pg
import numpy as np

class TelemetryPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(900, 300)
        self.move(35, 205)
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)

        self.status_label = QLabel("Status: Descending")
        self.altitude_label = QLabel("Altitude (Z): 1000 m")
        self.vert_speed_label = QLabel("Vertical Speed: -15 m/s")
        self.horiz_speed_label = QLabel("Horizontal Drift: 0 m/s")
        self.vel_mag_label = QLabel("Total Velocity: 15 m/s")
        self.attitude_label = QLabel("Attitude (Pitch, Roll, Yaw): (0°, 0°, 0°)")

        for lbl in [self.status_label, self.altitude_label, self.vert_speed_label,
                    self.horiz_speed_label, self.vel_mag_label, self.attitude_label]:
            lbl.setAlignment(Qt.AlignLeft)
            layout.addWidget(lbl)

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

    def update_telemetry(self, t, pos, vel, ori, status="Descending"):
        altitude = pos[1]
        vertical_speed = vel[1]
        horizontal_speed = np.linalg.norm([vel[0], vel[2]])
        velocity_magnitude = np.linalg.norm(vel)
        pitch, roll, yaw = np.degrees(ori)

        self.status_label.setText(f"Status: {status}")
        self.altitude_label.setText(f"Altitude (Z): {altitude:.2f} m")
        self.vert_speed_label.setText(f"Vertical Speed: {vertical_speed:.2f} m/s")
        self.horiz_speed_label.setText(f"Horizontal Drift: {horizontal_speed:.2f} m/s")
        self.vel_mag_label.setText(f"Total Velocity: {velocity_magnitude:.2f} m/s")
        self.attitude_label.setText(f"Attitude (Pitch, Roll, Yaw): ({pitch:.1f}°, {roll:.1f}°, {yaw:.1f}°)")

        self.time_data.append(t)
        self.altitude_data.append(altitude)
        self.altitude_curve.setData(self.time_data, self.altitude_data)