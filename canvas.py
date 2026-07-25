"""Rendering layer: draws the flock using QPainter, driven by a QTimer."""

import numpy as np
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QPainter, QColor, QPolygonF, QBrush
from PySide6.QtWidgets import QWidget

from simulation import Flock

BOID_SIZE = 6
BACKGROUND_COLOR = QColor(15, 15, 25)
BOID_COLOR = QColor(80, 200, 255)


class BoidsCanvas(QWidget):
    def __init__(self, flock: Flock, parent=None):
        super().__init__(parent)
        self.flock = flock
        self.setMinimumSize(int(flock.width), int(flock.height))

        self._base_triangle = [
            QPointF(BOID_SIZE, 0),
            QPointF(-BOID_SIZE * 0.6, BOID_SIZE * 0.5),
            QPointF(-BOID_SIZE * 0.6, -BOID_SIZE * 0.5),
        ]

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)
        self.timer.setInterval(16)

    def _on_tick(self):
        self.flock.update()
        self.update()

    def start(self):
        self.timer.start()

    def pause(self):
        self.timer.stop()

    def toggle(self):
        if self.timer.isActive():
            self.pause()
        else:
            self.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), BACKGROUND_COLOR)
        painter.setBrush(QBrush(BOID_COLOR))
        painter.setPen(Qt.NoPen)

        angles = self.flock.heading_angles()
        for (x, y), angle in zip(self.flock.positions, angles):
            painter.save()
            painter.translate(x, y)
            painter.rotate(np.degrees(angle))
            painter.drawPolygon(QPolygonF(self._base_triangle))
            painter.restore()

        painter.end()


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    flock = Flock(num_boids=40, seed=1)
    canvas = BoidsCanvas(flock)
    canvas.setWindowTitle("Boids Canvas - Static Check")
    canvas.show()
    sys.exit(app.exec())
