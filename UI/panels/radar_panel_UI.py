import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore


class RadarPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(600, 450)
        #self.move(35, parent.height() - 450 - 35)  # anchored bottom-left

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground((10, 30, 10))
        self.plot_widget.showGrid(x=True, y=True, alpha=0.2)
        self.plot_widget.getAxis('left').setPen(pg.mkPen((0, 255, 0), width=2))
        self.plot_widget.getAxis('bottom').setPen(pg.mkPen((0, 255, 0), width=2))
        self.plot_widget.hideAxis('left')
        self.plot_widget.hideAxis('bottom')
        self.plot_widget.setMouseEnabled(x=False, y=False)
        self.plot_widget.setMenuEnabled(False)
        half_width, half_height = 300, 225
        self.plot_widget.setXRange(-half_width, half_width)
        self.plot_widget.setYRange(-half_height, half_height)
        self.plot_widget.setAspectLocked(True)

        layout.addWidget(self.plot_widget)

        # Default cuboid
        self.base_shape_x = None
        self.base_shape_y = None
        self.lander_outline = None
        self.top_label = None

    def set_lander_dimensions(self, dimensions):
        """
        dimensions: (width, height, depth) in meters
        We'll use width and height for the top-down radar view.
        """
        width, height, _ = dimensions
        # Scale to fit radar panel 1 meter = 25 pixels
        scale = 25
        half_w = (width * scale) / 2
        half_h = (height * scale) / 2
        self.base_shape_x = np.array([-half_w, half_w, half_w, -half_w, -half_w])
        self.base_shape_y = np.array([-half_h, -half_h, half_h, half_h, -half_h])
        if self.lander_outline:
            self.plot_widget.removeItem(self.lander_outline)
        self.lander_outline = self.plot_widget.plot(
            self.base_shape_x,
            self.base_shape_y,
            pen=pg.mkPen((180, 255, 180), width=2),
            name="lander"
        )
        
        if self.top_label:
            self.plot_widget.removeItem(self.top_label)
        self.top_label = pg.TextItem(text="TOP", color=(0, 255, 0), anchor=(0.5, 0.7))
        self.top_label.setPos(0, half_h + 20)
        self.plot_widget.addItem(self.top_label)

    def update_attitude(self, roll=0, pitch=0, yaw=0):
        if self.base_shape_x is None or self.base_shape_y is None:
            return
        yaw = np.radians(yaw)
        rot_matrix = np.array([
            [np.cos(yaw), -np.sin(yaw)],
            [np.sin(yaw),  np.cos(yaw)]
        ])
        rotated = rot_matrix @ np.vstack([self.base_shape_x, self.base_shape_y])
        self.lander_outline.setData(rotated[0], rotated[1])
        
        # Rotate the "TOP" label with the craft
        if self.top_label:
            width, height, _ = self.base_shape_x[1] - self.base_shape_x[0], self.base_shape_y[2] - self.base_shape_y[1], 0
            half_h = (self.base_shape_y[2] - self.base_shape_y[1]) / 2
            # Label position at top of craft, rotated
            label_local_y = half_h + 20
            label_local_x = 0
            rotated_label_pos = rot_matrix @ np.array([label_local_x, label_local_y])
            self.top_label.setPos(rotated_label_pos[0], rotated_label_pos[1])

