"""Passive cable compilation for developed GrowingAnttisNeuron anatomy.

v1 keeps receiver dendrites fixed and lets development choose where sender inputs
land on those cables.  The cable physics itself is therefore arm-independent.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from .development import DevelopmentResult


@dataclass(frozen=True)
class PassiveCableConfig:
    """Normalized passive cable parameters used by the v1 bridge."""

    diameter: float = 0.018
    soma_area: float = 0.020
    capacitance_density: float = 1.0
    leak_density: float = 0.12
    axial_scale: float = 0.0025
    min_segment_length: float = 1e-3
    dt: float = 0.05
    degeneracy_rtol: float = 1e-8
    excitation_tol: float = 1e-12
    purity_target: float = 0.95

    def __post_init__(self) -> None:
        positive = (
            self.diameter,
            self.soma_area,
            self.capacitance_density,
            self.leak_density,
            self.axial_scale,
            self.min_segment_length,
            self.dt,
            self.degeneracy_rtol,
            self.excitation_tol,
        )
        if not all(math.isfinite(value) and value > 0.0 for value in positive):
            raise ValueError("passive cable parameters must be finite and positive")
        if not math.isfinite(self.purity_target) or not 0.0 < self.purity_target < 1.0:
            raise ValueError("purity_target must lie strictly between zero and one")


@dataclass(frozen=True, eq=False)
class ReceiverCable:
    """One receiver soma and its fixed dendritic sample points as a passive tree."""

    receiver: int
    positions: np.ndarray
    edges: np.ndarray
    capacitance: np.ndarray
    conductance: np.ndarray
    system_matrix: np.ndarray
    step_matrix: np.ndarray
    soma_index: int = 0


def _minimum_spanning_tree(positions: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    points = np.asarray(positions, dtype=float)
    if points.ndim != 2 or points.shape[1] != 2 or len(points) < 1:
        raise ValueError("positions must have shape (n, 2) with n >= 1")
    if not np.all(np.isfinite(points)):
        raise ValueError("positions must be finite")
    if len(points) == 1:
        return np.empty((0, 2), dtype=int), np.empty(0, dtype=float)

    candidates: list[tuple[float, int, int]] = []
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            distance = float(np.linalg.norm(points[i] - points[j]))
            candidates.append((distance, i, j))
    candidates.sort(key=lambda item: (item[0], item[1], item[2]))

    parent = list(range(len(points)))

    def find(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    selected: list[tuple[int, int]] = []
    lengths: list[float] = []
    for distance, i, j in candidates:
        root_i = find(i)
        root_j = find(j)
        if root_i == root_j:
            continue
        parent[root_j] = root_i
        selected.append((i, j))
        lengths.append(distance)
        if len(selected) == len(points) - 1:
            break

    if len(selected) != len(points) - 1:
        raise FloatingPointError("failed to build connected dendritic tree")
    return np.asarray(selected, dtype=int), np.asarray(lengths, dtype=float)


def _root_segment_lengths(
    n_nodes: int,
    edges: np.ndarray,
    lengths: np.ndarray,
    root: int = 0,
) -> np.ndarray:
    adjacency: list[list[tuple[int, float]]] = [[] for _ in range(n_nodes)]
    for (left, right), length in zip(edges, lengths):
        i, j = int(left), int(right)
        adjacency[i].append((j, float(length)))
        adjacency[j].append((i, float(length)))
    for neighbors in adjacency:
        neighbors.sort(key=lambda item: item[0])

    segment = np.zeros(n_nodes, dtype=float)
    seen = {root}
    queue = [root]
    while queue:
        node = queue.pop(0)
        for neighbor, length in adjacency[node]:
            if neighbor in seen:
                continue
            seen.add(neighbor)
            segment[neighbor] = length
            queue.append(neighbor)
    if len(seen) != n_nodes:
        raise FloatingPointError("dendritic tree is disconnected")
    return segment


def compile_receiver_cable(
    result: DevelopmentResult,
    receiver: int,
    config: PassiveCableConfig | None = None,
) -> ReceiverCable:
    """Compile one fixed receiver morphology into passive `C` and `G` matrices."""
    cfg = config or PassiveCableConfig()
    if isinstance(receiver, bool) or not isinstance(receiver, int):
        raise ValueError("receiver must be an integer index")
    if receiver < 0 or receiver >= len(result.receivers):
        raise ValueError("receiver index outside developed anatomy")

    soma = np.asarray(result.receivers[receiver].position, dtype=float)
    dendrites = [
        np.asarray(point.position, dtype=float)
        for point in result.dendrite_points
        if point.receiver == receiver
    ]
    positions = np.vstack([soma, *dendrites])
    edges, lengths = _minimum_spanning_tree(positions)
    rooted_lengths = _root_segment_lengths(len(positions), edges, lengths, root=0)

    area = np.empty(len(positions), dtype=float)
    area[0] = cfg.soma_area
    safe_rooted = np.maximum(rooted_lengths[1:], cfg.min_segment_length)
    area[1:] = np.pi * cfg.diameter * safe_rooted
    capacitance = cfg.capacitance_density * area

    conductance = np.empty(len(edges), dtype=float)
    system = np.diag(cfg.leak_density * area)
    for index, ((left, right), length) in enumerate(zip(edges, lengths)):
        safe_length = max(float(length), cfg.min_segment_length)
        axial = cfg.axial_scale * cfg.diameter * cfg.diameter / safe_length
        conductance[index] = axial
        i, j = int(left), int(right)
        system[i, i] += axial
        system[j, j] += axial
        system[i, j] -= axial
        system[j, i] -= axial

    c_matrix = np.diag(capacitance)
    step_matrix = np.linalg.solve(c_matrix + cfg.dt * system, c_matrix)

    if not np.all(np.isfinite(system)) or not np.all(np.isfinite(step_matrix)):
        raise FloatingPointError("passive cable compilation produced non-finite values")

    return ReceiverCable(
        receiver=receiver,
        positions=positions,
        edges=edges,
        capacitance=capacitance,
        conductance=conductance,
        system_matrix=system,
        step_matrix=step_matrix,
        soma_index=0,
    )


def whitened_modes(cable: ReceiverCable) -> tuple[np.ndarray, np.ndarray]:
    """Return generalized passive decay modes in a capacitance-whitened basis."""
    capacitance = np.asarray(cable.capacitance, dtype=float)
    system = np.asarray(cable.system_matrix, dtype=float)
    n = len(capacitance)
    if capacitance.shape != (n,) or system.shape != (n, n):
        raise ValueError("incompatible cable matrices")
    if np.any(capacitance <= 0.0) or not np.all(np.isfinite(capacitance)):
        raise ValueError("capacitance must be finite and positive")
    if not np.allclose(system, system.T, rtol=0.0, atol=1e-13):
        raise ValueError("system_matrix must be symmetric")

    inv_sqrt = np.diag(1.0 / np.sqrt(capacitance))
    whitened = inv_sqrt @ system @ inv_sqrt
    whitened = 0.5 * (whitened + whitened.T)
    values, vectors = np.linalg.eigh(whitened)
    order = np.argsort(values)
    values = values[order]
    vectors = vectors[:, order]
    if np.any(values <= 0.0):
        raise FloatingPointError("passive decay spectrum must be positive")
    return values, vectors
