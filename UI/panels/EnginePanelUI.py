from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QRadialGradient
from PyQt5.QtCore import Qt, QRectF
import math

class EnginePanel(QWidget):
    def __init__(self, lander=None, parent=None):
        super().__init__(parent)
        self.setFixedSize(450, 350)
        self.lander = lander

        # Labels
        self.lbl_active = QLabel(self)
        self.lbl_total = QLabel(self)
        self.lbl_per_engine = QLabel(self)
        for lbl in (self.lbl_active, self.lbl_total, self.lbl_per_engine):
            lbl.setStyleSheet("color: white; font-family: 'Helvetica'; background: transparent;")
            lbl.setWordWrap(True)

        self.lbl_active.move(14, 265)
        self.lbl_total.move(14, 285)
        self.lbl_per_engine.setGeometry(14, 305, 400, 40)

        self._title_font = QFont("Helvetica", 13, QFont.Bold)
        self._label_font = QFont("Helvetica", 9)

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)

    def update_panel(self):
        if not self.lander or not getattr(self.lander, "engines", None):
            self.lbl_per_engine.setText("")
            self.update()
            return

        engines = self.lander.engines
        active = sum(1 for e in engines if getattr(e, "enabled", True))
        total = sum(float(getattr(e, "current_thrust", 0.0)) for e in engines)
        per = [float(getattr(e, "current_thrust", 0.0)) for e in engines]
        self.lbl_per_engine.setText("Per-engine: " + ", ".join(f"{t:.0f}N" for t in per))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # --- Solid dark background ---
        p.setBrush(QColor(25, 25, 30))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(self.rect(), 10, 10)

        # --- Border ---
        rect = self.rect().adjusted(2, 2, -2, -2)
        p.setPen(QPen(QColor(80, 80, 85), 2))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(rect, 10, 10)

        # --- Title ---
        p.setFont(self._title_font)
        p.setPen(QColor(240, 240, 240))
        p.drawText(QRectF(0, 8, self.width(), 24), Qt.AlignCenter, "Engine Panel")

        # --- Visualization area ---
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

        # Try to get real or schematic positions
        positions = []
        try:
            coords = []
            for e in engines:
                pos = getattr(e, "position", None)
                coords.append((float(pos[0]), float(pos[2])) if pos and len(pos) >= 3 else (0.0, 0.0))
            dims = getattr(self.lander, "dimensions", None)
            if dims and len(dims) >= 3:
                half_w, half_d = float(dims[0]) / 2.0, float(dims[2]) / 2.0
            else:
                half_w = max(abs(x) for x, _ in coords) or 1
                half_d = max(abs(z) for _, z in coords) or 1
            outer_r = min(vis_w, vis_h) * 0.38
            for x, z in coords:
                sx, sz = x / half_w, z / half_d
                positions.append((cx + sx * outer_r, cy + sz * outer_r))
        except Exception:
            outer_r = 80
            for i in range(n):
                theta = 2 * math.pi * i / n
                positions.append((cx + outer_r * math.cos(theta),
                                  cy + outer_r * math.sin(theta)))

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

            if state == "off":
                p.setPen(QPen(QColor(130, 130, 130), 1.2))
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(QRectF(x - icon_r, y - icon_r, 2*icon_r, 2*icon_r))

            elif state == "on":
                # subtle glow (light gray, not white)
                glow_r = icon_r * 1.6
                grad = QRadialGradient(x, y, glow_r)
                grad.setColorAt(0, QColor(180, 180, 180, 80))
                grad.setColorAt(1, QColor(180, 180, 180, 0))
                p.setBrush(grad)
                p.setPen(Qt.NoPen)
                p.drawEllipse(QRectF(x - glow_r, y - glow_r, 2*glow_r, 2*glow_r))

                # engine body
                p.setBrush(QColor(40, 40, 40))
                p.setPen(QPen(QColor(20, 20, 20), 1))
                p.drawEllipse(QRectF(x - icon_r, y - icon_r, 2*icon_r, 2*icon_r))

                # inner fill proportional to thrust
                max_t = float(getattr(e, "max_thrust", 1.0)) if e else 1.0
                throttle = max(0.0, min(1.0, thrust / max_t))
                inner_r = icon_r * 0.8 * throttle
                if inner_r > 0.0:
                    p.setBrush(QColor(220, 220, 220))
                    p.setPen(Qt.NoPen)
                    p.drawEllipse(QRectF(x - inner_r, y - inner_r, 2*inner_r, 2*inner_r))

            elif state == "faulty":
                p.setPen(QPen(QColor(120, 90, 0), 2))
                p.setBrush(QColor(255, 215, 0))
                p.drawEllipse(QRectF(x - icon_r, y - icon_r, 2*icon_r, 2*icon_r))

            elif state == "failed":
                p.setPen(QPen(QColor(160, 0, 0), 2))
                p.setBrush(QColor(200, 0, 0))
                p.drawEllipse(QRectF(x - icon_r, y - icon_r, 2*icon_r, 2*icon_r))

        # --- Power bar ---
        bar_x = vis_left + vis_w + 20
        bar_y = vis_top
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
        p.drawRoundedRect(QRectF(bar_x + 3, fill_top + 3, bar_w - 6, max(3, fill_h - 6)), 3, 3)

        # Text percentage
        p.setFont(self._label_font)
        p.setPen(QColor(240, 240, 240))
        pct_text = f"{int(pct*100)}%"
        text_rect = QRectF(bar_x + bar_w + 6, bar_y + bar_h/2 - 12, 60, 24)
        p.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, pct_text)

        p.end()
