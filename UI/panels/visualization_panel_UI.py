from PyQt5.QtWidgets import QWidget, QVBoxLayout
from vispy import scene
from vispy.geometry import create_box

class VisualizationPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        self.canvas = scene.SceneCanvas(keys="interactive", bgcolor="black", size=(400, 400), show=True)
        layout.addWidget(self.canvas.native)

        view = self.canvas.central_widget.add_view()
        vertices, faces, _ = create_box()
        self.mesh = scene.visuals.Mesh(vertices=vertices["position"], faces=faces, color=(0.7, 0.7, 1, 1))
        view.add(self.mesh)
        view.camera = "turntable"  # rotate with mouse

        self.setLayout(layout)

    def update_attitude(self, rotation_matrix):
        """Apply rotation to the lander (placeholder)."""
        self.mesh.transform = rotation_matrix