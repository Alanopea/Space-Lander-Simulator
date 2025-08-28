import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore


class RadarPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(600, 450)
        self.move(35, parent.height() - 450 - 35)  # anchored bottom-left

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Radar-like plot
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground((10, 30, 10))  # dark green background

        # Grid styling
        self.plot_widget.showGrid(x=True, y=True, alpha=0.2)
        self.plot_widget.getAxis('left').setPen(pg.mkPen((0, 255, 0), width=2))
        self.plot_widget.getAxis('bottom').setPen(pg.mkPen((0, 255, 0), width=2))
        self.plot_widget.setMouseEnabled(x=False, y=False)
        self.plot_widget.setMenuEnabled(False)

        # Lock radar coordinate system to pixels (centered at 0,0)
        half_width, half_height = 300, 225   # half of panel size in px
        self.plot_widget.setXRange(-half_width, half_width)
        self.plot_widget.setYRange(-half_height, half_height)
        self.plot_widget.setAspectLocked(True)

        # Example lander outline (normalized ~100x100 px)
        self.lander_size = 100
        half_size = self.lander_size / 2
        self.base_shape_x = np.array([-half_size, half_size, half_size, -half_size, -half_size])
        self.base_shape_y = np.array([-half_size, -half_size, half_size, half_size, -half_size])

        self.lander_outline = self.plot_widget.plot(
            self.base_shape_x,
            self.base_shape_y,
            pen=pg.mkPen((180, 255, 180), width=2),
            name="lander"
        )

        layout.addWidget(self.plot_widget)

    def update_attitude(self, roll=0, pitch=0, yaw=0):
        """
        Rotate/tilt the lander shape.
        Angles in degrees.
        """
        # Convert to radians
        roll = np.radians(roll)
        pitch = np.radians(pitch)
        yaw = np.radians(yaw)

        # For 2D radar, we mainly show yaw (rotation in XY plane),
        # but we can also skew with pitch/roll if needed.
        rot_matrix = np.array([
            [np.cos(yaw), -np.sin(yaw)],
            [np.sin(yaw),  np.cos(yaw)]
        ])

        rotated = rot_matrix @ np.vstack([self.base_shape_x, self.base_shape_y])
        self.lander_outline.setData(rotated[0], rotated[1])

