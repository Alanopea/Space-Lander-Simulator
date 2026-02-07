from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel
from PyQt5.QtCore import Qt
import numpy as np

class TelemetryPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 900px wide, 300px tall (horizontal x vertical)
        self.setFixedSize(600, 500)
        # place 30px from left, 200px from top of dashboard
        #self.move(30, 200)

        grid = QGridLayout()
        grid.setContentsMargins(12, 12, 12, 12)
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(6)

        # Labels (left column = name, right column = value)
        labels = [
            "Altitude (m)",
            "Vertical Velocity (m/s)",
            "Horizontal Velocity (m/s)",
            "Total Speed (m/s)",
            "Acceleration (m/s²)",
            "Orientation (Pitch, Roll, Yaw) (°)",
            "Angular Velocity (°/s)",
            "Total Mass (kg)",
            "Dry Mass (kg)",
            "Fuel Remaining (kg)",
            "Fuel Capacity (kg)",
            "Fuel Remaining (%)",
            "Fuel Consumption Rate (kg/s)"
        ]
        self.value_labels = {}
        for i, name in enumerate(labels):
            name_lbl = QLabel(name)
            name_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            val_lbl = QLabel("N/A")
            val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(name_lbl, i, 0)
            grid.addWidget(val_lbl, i, 1)
            self.value_labels[name] = val_lbl

        self.setLayout(grid)

        # For computing derivatives
        self._prev_time = None
        self._prev_vel = None
        self._prev_ori = None  # assumed Euler angles in radians

    def update_telemetry(self, t, pos, vel, ori, total_mass=None, fuel_mass=None, initial_fuel_mass=None, 
                        fuel_consumption_rate=None, dry_mass=None):
        """
        t      : time (seconds)
        pos    : position array-like [x, z, y] or [x, y, z] (uses pos[1] as altitude as in project)
        vel    : velocity array-like [vx, vy, vz] (uses vel[1] as vertical)
        ori    : euler angles array-like (radians) [pitch, roll, yaw] expected
        total_mass, fuel_mass, initial_fuel_mass, fuel_consumption_rate, dry_mass : optional numeric telemetry values
        """
        # Ensure numpy arrays
        pos = np.asarray(pos, dtype=float)
        vel = np.asarray(vel, dtype=float)
        ori = np.asarray(ori, dtype=float)

        # Altitude (using pos[1] like your project)
        altitude = float(pos[1])
        vert_v = float(vel[1])
        horiz_v = float(np.linalg.norm([vel[0], vel[2]]))
        total_speed = float(np.linalg.norm(vel))

        # Time delta for derivatives
        accel = None
        ang_vel = None
        if self._prev_time is None:
            dt = None
        else:
            dt = t - self._prev_time if t is not None else None

        if dt and dt > 0 and self._prev_vel is not None:
            accel_vec = (vel - self._prev_vel) / dt
            accel = float(np.linalg.norm(accel_vec))
        else:
            accel = 0.0

        if dt and dt > 0 and self._prev_ori is not None:
            # Compute angular velocity (deg/s) from change in Euler angles
            delta_ori = ori - self._prev_ori
            ang_vel_vec = np.degrees(delta_ori / dt)
            ang_vel = float(np.linalg.norm(ang_vel_vec))
        else:
            ang_vel = 0.0

        # Orientation in degrees (pitch, roll, yaw)
        orient_deg = tuple(np.degrees(ori))
        # Normalize angles to 0-360 range
        orient_deg = tuple(angle % 360 for angle in orient_deg)
        orient_str = f"{orient_deg[0]:.1f}°, {orient_deg[1]:.1f}°, {orient_deg[2]:.1f}°"

        # Mass and fuel display
        total_mass_str = f"{total_mass:.1f}" if total_mass is not None else "N/A"
        dry_mass_str = f"{dry_mass:.1f}" if dry_mass is not None else "N/A"
        fuel_kg_str = f"{fuel_mass:.1f}" if fuel_mass is not None else "N/A"
        fuel_capacity_str = f"{initial_fuel_mass:.1f}" if initial_fuel_mass is not None else "N/A"
        
        if fuel_mass is not None and initial_fuel_mass is not None and initial_fuel_mass > 0:
            fuel_pct = (fuel_mass / initial_fuel_mass) * 100.0
            fuel_pct_str = f"{fuel_pct:.1f}"
        else:
            fuel_pct_str = "N/A"
        
        fuel_consumption_str = f"{fuel_consumption_rate:.2f}" if fuel_consumption_rate is not None else "N/A"

        # Update UI
        self.value_labels["Altitude (m)"].setText(f"{altitude:.2f}")
        self.value_labels["Vertical Velocity (m/s)"].setText(f"{vert_v:.2f}")
        self.value_labels["Horizontal Velocity (m/s)"].setText(f"{horiz_v:.2f}")
        self.value_labels["Total Speed (m/s)"].setText(f"{total_speed:.2f}")
        self.value_labels["Acceleration (m/s²)"].setText(f"{accel:.2f}")
        self.value_labels["Orientation (Pitch, Roll, Yaw) (°)"].setText(orient_str)
        self.value_labels["Angular Velocity (°/s)"].setText(f"{ang_vel:.2f}")
        self.value_labels["Total Mass (kg)"].setText(total_mass_str)
        self.value_labels["Dry Mass (kg)"].setText(dry_mass_str)
        self.value_labels["Fuel Remaining (kg)"].setText(fuel_kg_str)
        self.value_labels["Fuel Capacity (kg)"].setText(fuel_capacity_str)
        self.value_labels["Fuel Remaining (%)"].setText(fuel_pct_str)
        self.value_labels["Fuel Consumption Rate (kg/s)"].setText(fuel_consumption_str)

        # Save previous sample
        self._prev_time = t
        self._prev_vel = vel.copy()
        self._prev_ori = ori.copy()