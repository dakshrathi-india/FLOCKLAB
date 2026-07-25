"""Control panel: sliders/buttons wired to simulation parameters via signals/slots."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QPushButton,
    QSpinBox,
    QCheckBox,
)

from simulation import Flock
from canvas import BoidsCanvas


def _labeled_slider(name, min_val, max_val, initial, scale=1.0):
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)

    label = QLabel(f"{name}: {initial / scale:.2f}")
    slider = QSlider(Qt.Horizontal)
    slider.setMinimum(int(min_val * scale))
    slider.setMaximum(int(max_val * scale))
    slider.setValue(int(initial * scale))

    layout.addWidget(label)
    layout.addWidget(slider)
    return container, label, slider


class ControlPanel(QWidget):
    def __init__(self, flock: Flock, canvas: BoidsCanvas, parent=None):
        super().__init__(parent)
        self.flock = flock
        self.canvas = canvas

        root = QVBoxLayout(self)

        button_row = QHBoxLayout()
        self.play_button = QPushButton("Pause")
        self.play_button.clicked.connect(self._on_toggle_play)
        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(self._on_reset)
        button_row.addWidget(self.play_button)
        button_row.addWidget(reset_button)
        root.addLayout(button_row)

        count_row = QHBoxLayout()
        count_row.addWidget(QLabel("Number of boids:"))
        self.count_spin = QSpinBox()
        self.count_spin.setRange(2, 500)
        self.count_spin.setValue(flock.num_boids)
        self.count_spin.valueChanged.connect(self._on_count_changed)
        count_row.addWidget(self.count_spin)
        root.addLayout(count_row)

        self.grid_checkbox = QCheckBox("Use spatial grid (faster at high boid counts)")
        self.grid_checkbox.setChecked(flock.use_spatial_grid)
        self.grid_checkbox.stateChanged.connect(self._on_grid_toggled)
        root.addWidget(self.grid_checkbox)

        self.sep_container, self.sep_label, self.sep_slider = _labeled_slider(
            "Separation weight", 0.0, 5.0, flock.separation_weight, scale=100
        )
        self.align_container, self.align_label, self.align_slider = _labeled_slider(
            "Alignment weight", 0.0, 5.0, flock.alignment_weight, scale=100
        )
        self.coh_container, self.coh_label, self.coh_slider = _labeled_slider(
            "Cohesion weight", 0.0, 5.0, flock.cohesion_weight, scale=100
        )
        self.radius_container, self.radius_label, self.radius_slider = _labeled_slider(
            "Perception radius", 10, 200, flock.perception_radius, scale=1
        )

        self.sep_slider.valueChanged.connect(self._on_separation_changed)
        self.align_slider.valueChanged.connect(self._on_alignment_changed)
        self.coh_slider.valueChanged.connect(self._on_cohesion_changed)
        self.radius_slider.valueChanged.connect(self._on_radius_changed)

        for container in (
            self.sep_container,
            self.align_container,
            self.coh_container,
            self.radius_container,
        ):
            root.addWidget(container)

        root.addStretch()

    def _on_toggle_play(self):
        self.canvas.toggle()
        self.play_button.setText("Pause" if self.canvas.timer.isActive() else "Resume")

    def _on_reset(self):
        self.flock.set_num_boids(self.flock.num_boids)
        self.canvas.update()

    def _on_count_changed(self, value):
        self.flock.set_num_boids(value)
        self.canvas.update()

    def _on_grid_toggled(self, state):
        self.flock.use_spatial_grid = bool(state)

    def _on_separation_changed(self, value):
        self.flock.separation_weight = value / 100.0
        self.sep_label.setText(f"Separation weight: {value / 100.0:.2f}")

    def _on_alignment_changed(self, value):
        self.flock.alignment_weight = value / 100.0
        self.align_label.setText(f"Alignment weight: {value / 100.0:.2f}")

    def _on_cohesion_changed(self, value):
        self.flock.cohesion_weight = value / 100.0
        self.coh_label.setText(f"Cohesion weight: {value / 100.0:.2f}")

    def _on_radius_changed(self, value):
        self.flock.perception_radius = float(value)
        self.radius_label.setText(f"Perception radius: {value:.2f}")
