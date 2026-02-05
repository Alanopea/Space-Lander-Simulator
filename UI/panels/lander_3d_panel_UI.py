import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout

try:
    import pyqtgraph.opengl as gl
    from pyqtgraph import Vector
    from pyqtgraph.opengl import GLTextItem
except ImportError:  # pragma: no cover
    gl = None
    Vector = None
    GLTextItem = None


class Lander3DPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._enabled = gl is not None
        if not self._enabled:
            return

        # ---------------- VIEW ----------------
        self.view = gl.GLViewWidget()
        self.view.setBackgroundColor((0, 0, 0, 255))
        self.view.opts["distance"] = 35
        self.view.opts["elevation"] = 25   # slightly higher default
        self.view.opts["azimuth"] = 40
        if Vector is not None:
            self.view.opts["center"] = Vector(0, 0, 0)
        layout.addWidget(self.view)

        self._camera_smooth = 0.15

        # ---------------- GROUND ----------------
        # Simple grey ground square at y = 0
        ground_vertices = np.array([
            [-15, 0, -15],
            [15, 0, -15],
            [15, 0, 15],
            [-15, 0, 15],
            [-15, 0, -15],
        ], dtype=float)

        self.ground_square = gl.GLLinePlotItem(
            pos=ground_vertices,
            color=(150, 150, 150, 255),
            width=2,
            antialias=True,
            mode="line_strip",
        )
        self.view.addItem(self.ground_square)

        # Subtle grey grid on the ground plane
        self.grid = gl.GLGridItem()
        self.grid.setSize(500, 500)
        self.grid.setSpacing(2, 2)
        try:
            self.grid.setColor((80, 80, 80, 255))
        except Exception:
            pass
        self.view.addItem(self.grid)

        # ---------------- LANDER ----------------
        self._scale_geom = 0.25
        self._lander_dims = np.array([4.0, 10.0, 4.0], dtype=float)
        self._engine_body_positions = np.zeros((0, 3))
        self._lander_world_y = 0.0
        self._last_orientation = np.zeros(3)

        self.lander_wire = gl.GLLinePlotItem(
            pos=np.zeros((0, 3)),
            color=(255, 255, 255, 255),
            width=2,
            antialias=True,
            mode="lines",
        )
        self.view.addItem(self.lander_wire)

        self.engine_cones = []

        # ---------------- FORCES ----------------
        # Scale physical force magnitudes into view-space units
        self._force_scale = 0.02
        self.thrust_vec = self._create_force_item((0, 255, 0, 255))      # green
        self.gravity_vec = self._create_force_item((255, 0, 0, 255))     # red
        self.drag_vec = self._create_force_item((0, 128, 255, 255))      # blue
        self.net_vec = self._create_force_item((255, 255, 0, 255))       # yellow

        self._update_lander_geometry()

    def is_enabled(self):
        return self._enabled

    def set_lander_dimensions(self, dims):
        arr = np.asarray(dims, float)
        if arr.shape == (3,) and np.all(arr > 0):
            self._lander_dims = arr

    def set_engine_layout(self, positions):
        arr = np.asarray(positions, float)
        if arr.ndim == 2 and arr.shape[1] == 3:
            self._engine_body_positions = arr

    def update_scene(self, altitude_m, orientation_rad, forces):
        if not self._enabled:
            return

        try:
            ori = np.asarray(orientation_rad, float).reshape(3)
        except Exception:
            ori = self._last_orientation

        self._last_orientation = ori

        # Map simulator altitude (which is the lander COM height above ground)
        # so that y=0 in the view corresponds to the *bottom* of the lander,
        # not its center. When altitude_m == 0, the bottom of the cuboid sits
        # exactly on the ground plane.
        h_world = float(self._lander_dims[1]) * self._scale_geom
        half_h = h_world / 2.0
        # World-space COM height: ground (0) + half height + scaled altitude
        self._lander_world_y = max(half_h, altitude_m * self._scale_geom + half_h)

        self._update_lander_geometry(ori)

        forces = forces or {}
        self._update_force_item(self.thrust_vec, forces.get("thrust"))
        self._update_force_item(self.gravity_vec, forces.get("gravity"))
        self._update_force_item(self.drag_vec, forces.get("drag"))
        self._update_force_item(self.net_vec, forces.get("net"))

        self._focus_camera_on_lander()

    # ------------------------------------------------------------------
    # CAMERA
    # ------------------------------------------------------------------
    def _clamp_camera_angles(self):
        """
        Keep camera 'up' aligned with +Y so the ground (y=0) always appears at
        the bottom of the view. We allow azimuth to be freely rotated around
        the vertical axis, but we clamp elevation to avoid flipping the view.
        """
        elev = float(self.view.opts.get("elevation", 25.0))
        # prevent camera going below horizon or looking straight down
        self.view.opts["elevation"] = max(5.0, min(80.0, elev))

    def _focus_camera_on_lander(self):
        try:
            # Follow the lander vertically so it stays in view, but keep the
            # camera's up-direction fixed so the ground is always visually
            # "below" the lander in the viewport.
            target_y = float(self._lander_world_y)

            if Vector is not None:
                self.view.opts["center"] = Vector(0, target_y, 0)
            else:
                # Fallback: a plain tuple is accepted by GLViewWidget
                self.view.opts["center"] = (0.0, target_y, 0.0)

            # Lock elevation to a reasonable range on every update so user
            # interaction cannot flip the ground above the lander.
            self._clamp_camera_angles()

        except Exception:
            pass

    # ------------------------------------------------------------------
    # LANDER GEOMETRY
    # ------------------------------------------------------------------
    def _update_lander_geometry(self, orientation=None):
        verts = self._build_cuboid_vertices()

        if orientation is not None:
            R = self._euler_to_matrix(orientation)
            verts = (R @ verts.T).T
        else:
            R = np.eye(3)

        verts[:, 1] += self._lander_world_y
        self.lander_wire.setData(pos=verts)

        self._rebuild_engines(R)

    def _build_cuboid_vertices(self):
        w, h, d = self._lander_dims * self._scale_geom
        hw, hh, hd = w / 2, h / 2, d / 2

        return np.array([
            [-hw,-hh,-hd],[ hw,-hh,-hd],[ hw,-hh, hd],[-hw,-hh, hd],[-hw,-hh,-hd],
            [-hw, hh,-hd],[ hw, hh,-hd],[ hw, hh, hd],[-hw, hh, hd],[-hw, hh,-hd],
            [-hw,-hh,-hd],[-hw, hh,-hd],
            [ hw,-hh,-hd],[ hw, hh,-hd],
            [ hw,-hh, hd],[ hw, hh, hd],
            [-hw,-hh, hd],[-hw, hh, hd],
        ])

    # ------------------------------------------------------------------
    # ENGINES
    # ------------------------------------------------------------------
    def _rebuild_engines(self, R):
        for c in self.engine_cones:
            self.view.removeItem(c)
        self.engine_cones.clear()

        for pos in self._engine_body_positions:
            world = R @ (pos * self._scale_geom)
            world[1] += self._lander_world_y
            cone = self._create_engine_cone(world)
            self.view.addItem(cone)
            self.engine_cones.append(cone)

    def _create_engine_cone(self, pos):
        r, h, n = 0.4, 1.0, 16
        ang = np.linspace(0, 2*np.pi, n)

        circle = np.vstack([
            r*np.cos(ang),
            -np.ones(n)*h,
            r*np.sin(ang)
        ]).T

        apex = np.array([[0, h, 0]])

        edges = []
        for i in range(n-1):
            edges += [circle[i], circle[i+1]]
        edges += [circle[-1], circle[0]]

        for p in circle:
            edges += [p, apex[0]]

        edges = np.array(edges) + pos

        return gl.GLLinePlotItem(
            pos=edges,
            color=(255,255,255,255),
            width=1.5,
            antialias=True,
            mode="lines"
        )

    # ------------------------------------------------------------------
    # FORCE VECTORS
    # ------------------------------------------------------------------
    def _create_force_item(self, color_rgba):
        item = gl.GLLinePlotItem(
            pos=np.zeros((2, 3), dtype=float),
            color=color_rgba,
            width=3,
            antialias=True,
            mode="lines",
        )
        self.view.addItem(item)
        return item

    def _update_force_item(self, item, vec):
        if not self._enabled or item is None:
            return

        if vec is None:
            pos = np.zeros((2, 3), dtype=float)
        else:
            try:
                v = np.asarray(vec, dtype=float).reshape(3)
            except Exception:
                pos = np.zeros((2, 3), dtype=float)
            else:
                origin = np.array([0.0, self._lander_world_y, 0.0], dtype=float)
                end = origin + v * self._force_scale
                pos = np.vstack([origin, end])

        item.setData(pos=pos)

    # ------------------------------------------------------------------
    # ROTATION
    # ------------------------------------------------------------------
    @staticmethod
    def _euler_to_matrix(a):
        pitch, roll, yaw = a
        cp, sp = np.cos(pitch), np.sin(pitch)
        cr, sr = np.cos(roll), np.sin(roll)
        cy, sy = np.cos(yaw), np.sin(yaw)

        Rz = np.array([[cy,-sy,0],[sy,cy,0],[0,0,1]])
        Rx = np.array([[1,0,0],[0,cr,-sr],[0,sr,cr]])
        Ry = np.array([[cp,0,sp],[0,1,0],[-sp,0,cp]])

        return Rz @ Rx @ Ry
