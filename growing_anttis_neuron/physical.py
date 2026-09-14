"""Passive cable compilation and developed-input modal diagnostics.

v1 keeps receiver dendrites fixed and lets development choose where sender inputs
land on those cables.  The cable physics itself is therefore arm-independent.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from .development import DevelopmentResult, Synapse


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


@dataclass(frozen=True)
class SynapsePhysicalMetrics:
    """Physical diagnostics for one developed synaptic input port."""

    compartment: int
    visible_mode_effective_count: float
    slow_target_decay: float | None
    next_decay_gap: float | None
    purification_time_95: float | None
    soma_transfer_resistance: float


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


def synapse_compartment(
    result: DevelopmentResult,
    synapse: Synapse,
    cable: ReceiverCable,
) -> int:
    """Map a developed contact to the nearest dendritic cable compartment."""
    if cable.receiver != synapse.receiver:
        raise ValueError("synapse and cable must belong to the same receiver")
    if synapse.receiver < 0 or synapse.receiver >= len(result.receivers):
        raise ValueError("synapse receiver outside developed anatomy")
    if len(cable.positions) <= 1:
        raise ValueError("receiver cable has no dendritic compartments")

    contact = np.asarray([synapse.x, synapse.y], dtype=float)
    if not np.all(np.isfinite(contact)):
        raise ValueError("synapse contact must be finite")
    distances = np.sum((cable.positions[1:] - contact) ** 2, axis=1)
    return 1 + int(np.argmin(distances))


def _same_decay(left: float, right: float, rtol: float) -> bool:
    return abs(left - right) <= rtol * max(1.0, abs(left), abs(right))


def _group_excited_modes(
    decays: np.ndarray,
    energies: np.ndarray,
    *,
    degeneracy_rtol: float,
    excitation_tol: float,
) -> tuple[np.ndarray, np.ndarray]:
    d = np.asarray(decays, dtype=float)
    e = np.asarray(energies, dtype=float)
    if d.ndim != 1 or e.ndim != 1 or d.shape != e.shape:
        raise ValueError("decays and energies must be same-length vectors")
    if not np.all(np.isfinite(d)) or np.any(d < 0.0):
        raise ValueError("decays must be finite and non-negative")
    if not np.all(np.isfinite(e)) or np.any(e < 0.0):
        raise ValueError("energies must be finite and non-negative")
    if not math.isfinite(degeneracy_rtol) or degeneracy_rtol <= 0.0:
        raise ValueError("degeneracy_rtol must be finite and positive")
    if not math.isfinite(excitation_tol) or excitation_tol <= 0.0:
        raise ValueError("excitation_tol must be finite and positive")

    keep = e > excitation_tol
    if not np.any(keep):
        return np.empty(0, dtype=float), np.empty(0, dtype=float)
    d = d[keep]
    e = e[keep]
    order = np.argsort(d, kind="stable")
    d = d[order]
    e = e[order]

    grouped_decay: list[float] = []
    grouped_energy: list[float] = []
    start = 0
    while start < len(d):
        stop = start + 1
        while stop < len(d) and _same_decay(float(d[stop - 1]), float(d[stop]), degeneracy_rtol):
            stop += 1
        grouped_decay.append(float(np.mean(d[start:stop])))
        grouped_energy.append(float(np.sum(e[start:stop])))
        start = stop
    return np.asarray(grouped_decay, dtype=float), np.asarray(grouped_energy, dtype=float)


def purification_time(
    decays: np.ndarray,
    energies: np.ndarray,
    *,
    purity_target: float,
    degeneracy_rtol: float,
    excitation_tol: float,
) -> float | None:
    """Time until the slowest excited eigenspace carries the requested energy fraction."""
    if not math.isfinite(purity_target) or not 0.0 < purity_target < 1.0:
        raise ValueError("purity_target must lie strictly between zero and one")
    grouped_decay, grouped_energy = _group_excited_modes(
        decays,
        energies,
        degeneracy_rtol=degeneracy_rtol,
        excitation_tol=excitation_tol,
    )
    if len(grouped_decay) == 0:
        return None
    if len(grouped_decay) == 1:
        return 0.0

    target_decay = float(grouped_decay[0])
    target_energy = float(grouped_energy[0])
    relative_decay = grouped_decay[1:] - target_decay
    if np.any(relative_decay <= 0.0):
        raise FloatingPointError("eigenspace grouping failed to separate decay rates")

    def purity(time: float) -> float:
        faster = np.sum(grouped_energy[1:] * np.exp(-2.0 * relative_decay * time))
        return target_energy / (target_energy + float(faster))

    if purity(0.0) >= purity_target:
        return 0.0
    upper = 1.0
    for _ in range(256):
        if purity(upper) >= purity_target:
            break
        upper *= 2.0
    else:
        raise FloatingPointError("failed to bracket passive purification time")

    lower = 0.0
    for _ in range(100):
        midpoint = 0.5 * (lower + upper)
        if purity(midpoint) >= purity_target:
            upper = midpoint
        else:
            lower = midpoint
    return float(upper)


def _effective_count(energies: np.ndarray, excitation_tol: float) -> float:
    values = np.asarray(energies, dtype=float)
    values = values[values > excitation_tol]
    if len(values) == 0:
        return 0.0
    probabilities = values / float(np.sum(values))
    entropy = -float(np.sum(probabilities * np.log(probabilities)))
    return float(math.exp(entropy))


def synapse_physical_metrics(
    result: DevelopmentResult,
    synapse: Synapse,
    config: PassiveCableConfig | None = None,
) -> SynapsePhysicalMetrics:
    """Measure how one developed synaptic port couples into passive receiver modes."""
    cfg = config or PassiveCableConfig()
    cable = compile_receiver_cable(result, synapse.receiver, cfg)
    compartment = synapse_compartment(result, synapse, cable)
    decays, vectors = whitened_modes(cable)

    weighted_uniform = np.sqrt(cable.capacitance)
    weighted_uniform /= float(np.linalg.norm(weighted_uniform))
    uniform_index = int(np.argmax(np.abs(vectors.T @ weighted_uniform)))
    keep = np.ones(len(decays), dtype=bool)
    keep[uniform_index] = False
    nonuniform_decays = decays[keep]
    nonuniform_vectors = vectors[:, keep]

    forcing = np.zeros(len(cable.capacitance), dtype=float)
    forcing[compartment] = synapse.weight / math.sqrt(float(cable.capacitance[compartment]))
    amplitudes = nonuniform_vectors.T @ forcing
    energies = amplitudes * amplitudes
    effective_count = _effective_count(energies, cfg.excitation_tol)

    grouped_decay, _ = _group_excited_modes(
        nonuniform_decays,
        energies,
        degeneracy_rtol=cfg.degeneracy_rtol,
        excitation_tol=cfg.excitation_tol,
    )
    if len(grouped_decay) == 0:
        slow_target_decay: float | None = None
        next_decay_gap: float | None = None
    else:
        slow_target_decay = float(grouped_decay[0])
        next_decay_gap = (
            float(grouped_decay[1] - grouped_decay[0]) if len(grouped_decay) >= 2 else None
        )

    time_95 = purification_time(
        nonuniform_decays,
        energies,
        purity_target=cfg.purity_target,
        degeneracy_rtol=cfg.degeneracy_rtol,
        excitation_tol=cfg.excitation_tol,
    )

    point_current = np.zeros(len(cable.capacitance), dtype=float)
    point_current[compartment] = 1.0
    dc_voltage = np.linalg.solve(cable.system_matrix, point_current)
    soma_transfer = float(dc_voltage[cable.soma_index] * synapse.weight)
    if not math.isfinite(soma_transfer):
        raise FloatingPointError("non-finite soma transfer resistance")

    return SynapsePhysicalMetrics(
        compartment=compartment,
        visible_mode_effective_count=effective_count,
        slow_target_decay=slow_target_decay,
        next_decay_gap=next_decay_gap,
        purification_time_95=time_95,
        soma_transfer_resistance=soma_transfer,
    )
