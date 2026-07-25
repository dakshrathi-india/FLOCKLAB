"""Entry point. Run with: python main.py"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout

from simulation import Flock
from canvas import BoidsCanvas
from controls import ControlPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FlockLab - Boids Flocking Simulator")

        flock = Flock(num_boids=100, width=800, height=600, seed=None)
        self.canvas = BoidsCanvas(flock)
        self.controls = ControlPanel(flock, self.canvas)
        self.controls.setFixedWidth(260)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.addWidget(self.canvas, stretch=1)
        layout.addWidget(self.controls)
        self.setCentralWidget(central)

        self.canvas.start()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1080, 640)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
