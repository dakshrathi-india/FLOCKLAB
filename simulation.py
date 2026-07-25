"""Pure simulation logic for the Boids flocking model. No Qt dependency."""

import numpy as np


class SpatialGrid:
    """Bins boids into cells (size = perception radius) for fast neighbor lookup."""

    def __init__(self, width, height, cell_size):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.cols = max(1, int(np.ceil(width / cell_size)))
        self.rows = max(1, int(np.ceil(height / cell_size)))
        self.cells = {}

    def build(self, positions):
        self.cells.clear()
        cols = np.minimum((positions[:, 0] // self.cell_size).astype(int), self.cols - 1)
        rows = np.minimum((positions[:, 1] // self.cell_size).astype(int), self.rows - 1)
        for idx, (c, r) in enumerate(zip(cols, rows)):
            self.cells.setdefault((c, r), []).append(idx)

    def candidate_indices(self, position):
        c = min(int(position[0] // self.cell_size), self.cols - 1)
        r = min(int(position[1] // self.cell_size), self.rows - 1)
        candidates = []
        for dc in (-1, 0, 1):
            for dr in (-1, 0, 1):
                key = ((c + dc) % self.cols, (r + dr) % self.rows)
                candidates.extend(self.cells.get(key, []))
        return candidates


class Flock:
    """Holds all boid state as NumPy arrays for vectorized updates."""

    def __init__(self, num_boids=100, width=800, height=600, seed=None):
        self.width = width
        self.height = height
        rng = np.random.default_rng(seed)

        self.positions = rng.uniform(low=[0, 0], high=[width, height], size=(num_boids, 2))
        angles = rng.uniform(0, 2 * np.pi, size=num_boids)
        self.velocities = np.stack([np.cos(angles), np.sin(angles)], axis=1) * 2.0

        self.perception_radius = 60.0
        self.max_speed = 4.0
        self.max_force = 0.05

        self.separation_weight = 1.5
        self.alignment_weight = 1.0
        self.cohesion_weight = 1.0

        self.use_spatial_grid = False
        self._grid = SpatialGrid(width, height, cell_size=self.perception_radius)

    @property
    def num_boids(self):
        return self.positions.shape[0]

    def set_num_boids(self, n, seed=None):
        preserved_grid_setting = self.use_spatial_grid
        self.__init__(num_boids=n, width=self.width, height=self.height, seed=seed)
        self.use_spatial_grid = preserved_grid_setting

    def _pairwise_deltas_and_dists(self):
        deltas = self.positions[np.newaxis, :, :] - self.positions[:, np.newaxis, :]
        dists = np.linalg.norm(deltas, axis=2)
        return deltas, dists

    def _limit_magnitude(self, vectors, max_mag):
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        scale = np.where(norms > max_mag, max_mag / np.maximum(norms, 1e-8), 1.0)
        return vectors * scale

    def update(self):
        n = self.num_boids
        if n == 0:
            return

        if self.use_spatial_grid:
            steering = self._compute_steering_grid()
        else:
            steering = self._compute_steering_bruteforce()

        steering = self._limit_magnitude(steering, self.max_force)
        self.velocities += steering
        self.velocities = self._limit_magnitude(self.velocities, self.max_speed)
        self.positions += self.velocities

        self.positions[:, 0] %= self.width
        self.positions[:, 1] %= self.height

    def _compute_steering_bruteforce(self):
        deltas, dists = self._pairwise_deltas_and_dists()

        neighbor_mask = (dists > 1e-8) & (dists < self.perception_radius)
        neighbor_counts = neighbor_mask.sum(axis=1)
        has_neighbors = neighbor_counts > 0

        safe_dists = np.where(dists > 1e-8, dists, 1e-8)
        repulse = -deltas / (safe_dists[..., np.newaxis] ** 2)
        repulse = np.where(neighbor_mask[..., np.newaxis], repulse, 0.0)
        separation = repulse.sum(axis=1)

        masked_vel = np.where(neighbor_mask[..., np.newaxis], self.velocities[np.newaxis, :, :], 0.0)
        avg_vel = masked_vel.sum(axis=1)
        avg_vel[has_neighbors] /= neighbor_counts[has_neighbors, np.newaxis]
        alignment = avg_vel - self.velocities

        masked_delta = np.where(neighbor_mask[..., np.newaxis], deltas, 0.0)
        avg_delta = masked_delta.sum(axis=1)
        avg_delta[has_neighbors] /= neighbor_counts[has_neighbors, np.newaxis]
        cohesion = avg_delta

        no_neighbor = ~has_neighbors
        separation[no_neighbor] = 0.0
        alignment[no_neighbor] = 0.0
        cohesion[no_neighbor] = 0.0

        return (
            self.separation_weight * separation
            + self.alignment_weight * alignment
            + self.cohesion_weight * cohesion
        )

    def _compute_steering_grid(self):
        self._grid.cell_size = self.perception_radius
        self._grid.cols = max(1, int(np.ceil(self.width / self._grid.cell_size)))
        self._grid.rows = max(1, int(np.ceil(self.height / self._grid.cell_size)))
        self._grid.build(self.positions)

        n = self.num_boids
        steering = np.zeros((n, 2))

        for i in range(n):
            candidates = [j for j in self._grid.candidate_indices(self.positions[i]) if j != i]
            if not candidates:
                continue

            candidates = np.array(candidates)
            delta = self.positions[candidates] - self.positions[i]
            dist = np.linalg.norm(delta, axis=1)

            mask = dist < self.perception_radius
            if not mask.any():
                continue

            delta = delta[mask]
            dist = dist[mask]
            neighbor_vels = self.velocities[candidates][mask]

            safe_dist = np.maximum(dist, 1e-8)
            separation = (-delta / (safe_dist[:, np.newaxis] ** 2)).sum(axis=0)
            alignment = neighbor_vels.mean(axis=0) - self.velocities[i]
            cohesion = delta.mean(axis=0)

            steering[i] = (
                self.separation_weight * separation
                + self.alignment_weight * alignment
                + self.cohesion_weight * cohesion
            )

        return steering

    def heading_angles(self):
        return np.arctan2(self.velocities[:, 1], self.velocities[:, 0])


if __name__ == "__main__":
    flock = Flock(num_boids=50, seed=42)
    print(f"Initialized {flock.num_boids} boids")
    print("Initial mean position:", flock.positions.mean(axis=0))

    for step in range(5):
        flock.update()
        print(
            f"Step {step + 1}: mean position = {flock.positions.mean(axis=0)}, "
            f"mean speed = {np.linalg.norm(flock.velocities, axis=1).mean():.3f}"
        )

    import time

    print("\nBenchmark: brute-force vs spatial grid (avg ms per update)")
    print(f"{'N':>6} | {'brute-force':>12} | {'spatial grid':>12}")
    for n in (100, 300, 600, 1000):
        f1 = Flock(num_boids=n, width=1200, height=900, seed=0)
        f1.use_spatial_grid = False
        start = time.perf_counter()
        for _ in range(20):
            f1.update()
        brute_ms = (time.perf_counter() - start) / 20 * 1000

        f2 = Flock(num_boids=n, width=1200, height=900, seed=0)
        f2.use_spatial_grid = True
        start = time.perf_counter()
        for _ in range(20):
            f2.update()
        grid_ms = (time.perf_counter() - start) / 20 * 1000

        print(f"{n:>6} | {brute_ms:>10.2f}ms | {grid_ms:>10.2f}ms")
