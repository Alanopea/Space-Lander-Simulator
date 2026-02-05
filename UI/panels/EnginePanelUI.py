from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QRadialGradient
from PyQt5.QtCore import Qt, QRectF
import math

class EnginePanel(QWidget):
    def __init__(self, lander=None, parent=None):
        super().__init__(parent)
        self.setFixedSize(550, 350)
        self.lander = lander

        # Info labels (below visualization)
        self.lbl_active = QLabel(self)
        self.lbl_total = QLabel(self)
        self.lbl_per_engine = QLabel(self)
        for lbl in (self.lbl_active, self.lbl_total, self.lbl_per_engine):
            lbl.setStyleSheet("color: white; font-family: 'Helvetica';")
            lbl.setWordWrap(True)
        #self.lbl_active.move(14, 245)
        #self.lbl_total.move(14, 265)
        self.lbl_per_engine.setGeometry(14, 285, 500, 60)

        # Fonts and base style
        self._title_font = QFont("Helvetica", 13, QFont.Bold)
        self._label_font = QFont("Helvetica", 9)
        self.setAutoFillBackground(False)

    def update_panel(self):
        """Refresh info from lander and repaint"""
        if not self.lander or not getattr(self.lander, "engines", None):
            self.lbl_per_engine.setText("")
            self.update()
            return

        engines = self.lander.engines
        active = sum(1 for e in engines if getattr(e, "enabled", True))
        total = sum(float(getattr(e, "current_thrust", 0.0)) for e in engines)
        per = [float(getattr(e, "current_thrust", 0)) for e in engines]
        self.lbl_per_engine.setText("Per-engine: " + ", ".join(f"{t:.0f}N" for t in per))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # --- Panel background ---
        rect = self.rect().adjusted(2, 2, -2, -2)
        p.setBrush(QColor(20, 22, 25))
        p.setPen(QPen(QColor(80, 80, 85), 2))
        p.drawRoundedRect(rect, 10, 10)

        # --- Title ---
        p.setFont(self._title_font)
        p.setPen(QColor(230, 230, 230))
        p.drawText(QRectF(0, 8, self.width(), 50), Qt.AlignCenter, "Engine Panel")

        # --- Visualization center ---
        vis_left = 18
        vis_top = 38
        vis_w = 240
        vis_h = 190
        cx = vis_left + vis_w / 2.0
        cy = vis_top + vis_h / 2.0

        engines = getattr(self.lander, "engines", []) if self.lander else []
        n = len(engines)
        if n == 0:
            p.end()
            return

        # Map physical engine positions (x,z) into UI coordinates when available.
        positions = []
        try:
            coords = []
            for e in engines:
                pos = getattr(e, "position", None)
                if pos is None or len(pos) < 3:
                    coords.append((0.0, 0.0))
                else:
                    coords.append((float(pos[0]), float(pos[2])))

            # If lander dimensions provided, use them to normalize mapping for consistent scale
            dims = getattr(self.lander, "dimensions", None)
            if dims is not None and len(dims) >= 3:
                half_w = float(dims[0]) / 2.0
                half_d = float(dims[2]) / 2.0
            else:
                # compute max absolute coordinate to avoid zero-scale
                xs = [abs(x) for x, _ in coords]
                zs = [abs(z) for _, z in coords]
                half_w = max(xs) if xs else 0.0
                half_d = max(zs) if zs else 0.0

            max_dim = max(half_w, half_d, 1e-6)
            outer_r = min(vis_w, vis_h) * 0.38

            # If all positions near zero, fallback to schematic
            if all(math.hypot(x, z) < 1e-6 for x, z in coords):
                raise RuntimeError("fallback to schematic")

            # Map coords proportionally to outer_r
            for x, z in coords:
                sx = max(-1.0, min(1.0, x / max_dim))
                sz = max(-1.0, min(1.0, z / max_dim))
                positions.append((cx + sx * outer_r, cy + sz * outer_r))

            # If mapping produced fewer positions (shouldn't happen), fallback
            if len(positions) != n:
                raise RuntimeError("mapping mismatch")

        except Exception:
            # fallback schematic layout: center + outer ring (center-first if possible)
            positions = []
            if n == 1:
                positions.append((cx, cy))
            else:
                # prefer 1 center and rest in ring (matches Falcon9 center+8)
                inner_n = 1
                outer_n = n - inner_n
                inner_r = 20.0
                outer_r = 80.0
                # inner
                for i in range(inner_n):
                    theta = 2 * math.pi * i / max(1, inner_n)
                    positions.append((cx + inner_r * math.cos(theta),
                                      cy + inner_r * math.sin(theta)))
                # outer
                for i in range(outer_n):
                    theta = 2 * math.pi * i / max(1, outer_n)
                    positions.append((cx + outer_r * math.cos(theta),
                                      cy + outer_r * math.sin(theta)))

        # --- Draw engines ---
        icon_r = 10.0
        for i, pos in enumerate(positions):
            e = engines[i] if i < len(engines) else None
            x, y = pos
            state = "off"
            thrust = 0.0

            if e:
                enabled = bool(getattr(e, "enabled", True))
                status = getattr(e, "status", None)
                thrust = float(getattr(e, "current_thrust", 0.0))
                if status == "failed":
                    state = "failed"
                elif status == "faulty":
                    state = "faulty"
                elif enabled:
                    state = "on"
                else:
                    state = "off"

            if state == "off":
                p.setPen(QPen(QColor(130, 130, 130), 1.2))
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(QRectF(x - icon_r, y - icon_r, 2.0 * icon_r, 2.0 * icon_r))

            elif state == "on":
                glow_r = icon_r * 1.6
                grad = QRadialGradient(x, y, glow_r)
                grad.setColorAt(0, QColor(255, 255, 255, 60))
                grad.setColorAt(1, QColor(255, 255, 255, 0))
                p.setBrush(grad)
                p.setPen(Qt.NoPen)
                p.drawEllipse(QRectF(x - glow_r, y - glow_r, glow_r * 2.0, glow_r * 2.0))

                # outer ring
                p.setBrush(QColor(40, 40, 40))
                p.setPen(QPen(QColor(20, 20, 20), 1))
                p.drawEllipse(QRectF(x - icon_r, y - icon_r, 2.0 * icon_r, 2.0 * icon_r))

                # white inner fill proportional to thrust
                max_t = float(getattr(e, "max_thrust", 1.0)) if e else 1.0
                throttle = max(0.0, min(1.0, thrust / max_t))
                inner_r = icon_r * 0.8 * throttle
                if inner_r > 0.0:
                    p.setBrush(QColor(255, 255, 255))
                    p.setPen(Qt.NoPen)
                    p.drawEllipse(QRectF(x - inner_r, y - inner_r, 2.0 * inner_r, 2.0 * inner_r))


            elif state == "faulty":
                p.setPen(QPen(QColor(120, 90, 0), 2))
                p.setBrush(QColor(255, 215, 0))
                p.drawEllipse(QRectF(x - icon_r, y - icon_r, 2.0 * icon_r, 2.0 * icon_r))

            elif state == "failed":
                p.setPen(QPen(QColor(160, 0, 0), 2))
                p.setBrush(QColor(200, 0, 0))
                p.drawEllipse(QRectF(x - icon_r, y - icon_r, 2.0 * icon_r, 2.0 * icon_r))

        # --- Power bar ---
        bar_x = vis_left + vis_w + 100
        bar_y = vis_top + 20
        bar_w = 28
        bar_h = vis_h
        p.setPen(QPen(QColor(100, 100, 110), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), 4, 4)

        total_thrust = sum(float(getattr(e, "current_thrust", 0.0)) for e in engines)
        max_total = sum(float(getattr(e, "max_thrust", 0.0)) for e in engines) or 1.0
        pct = max(0.0, min(1.0, total_thrust / max_total))
        fill_h = int(bar_h * pct)
        fill_top = bar_y + (bar_h - fill_h)

        if pct < 0.6:
            color = QColor(60, 200, 90)
        elif pct < 0.85:
            color = QColor(230, 200, 60)
        else:
            color = QColor(230, 70, 70)

        p.setPen(Qt.NoPen)
        p.setBrush(color)
        if fill_h > 6:
            p.drawRoundedRect(QRectF(bar_x + 3, fill_top + 3, bar_w - 6, fill_h - 6), 3, 3)
        elif fill_h > 0:
            p.drawRect(QRectF(bar_x + 3, fill_top + 3, bar_w - 6, max(1, fill_h - 3)))

        # Text percentage (use QRectF)
        p.setFont(self._label_font)
        p.setPen(QColor(240, 240, 240))
        pct_text = f"{int(pct*100)}%"
        text_rect = QRectF(bar_x + bar_w + 6, bar_y + bar_h / 2 - 12, 60, 24)
        p.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, pct_text)

        p.end()