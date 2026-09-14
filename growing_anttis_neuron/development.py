"""Deterministic developmental geometry for GrowingAnttisNeuron v0.

The model is intentionally small. Receiver dendrites are fixed; sender axons
are the only structures that grow. Molecular vectors are continuous positional
coordinates, not neuron IDs.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Literal

import numpy as np

Arm = Literal["guided", "shuffled_labels", "random_walk"]


@dataclass(frozen=True)
class DevelopmentConfig:
    n_senders: int = 8
    n_receivers: int = 8
    steps: int = 56
    step_size: float = 0.025
    capture_radius: float = 0.05
    compatibility_sigma: float = 0.11
    compatibility_threshold: float = 0.72
    branch_probability: float = 0.045
    max_branches_per_sender: int = 2
    chemo_weight: float = 14.0
    persistence_weight: float = 0.22
    crowding_weight: float = 0.08
    crowding_radius: float = 0.035
    noise_weight: float = 0.035
    target_x: float = 0.78

    def __post_init__(self) -> None:
        if self.n_senders < 1 or self.n_receivers < 1:
            raise ValueError("sender and receiver counts must be positive")
        if self.steps < 1:
            raise ValueError("steps must be positive")
        if self.step_size <= 0.0:
            raise ValueError("step_size must be positive")
        if not 0.0 < self.capture_radius < 1.0:
            raise ValueError("capture_radius must be inside (0, 1)")
        if self.compatibility_sigma <= 0.0:
            raise ValueError("compatibility_sigma must be positive")
        if not 0.0 <= self.compatibility_threshold <= 1.0:
            raise ValueError("compatibility_threshold must be inside [0, 1]")
        if not 0.0 <= self.branch_probability <= 1.0:
            raise ValueError("branch_probability must be inside [0, 1]")
        if self.max_branches_per_sender < 0:
            raise ValueError("max_branches_per_sender must be nonnegative")


@dataclass(frozen=True, eq=False)
class Neuron:
    index: int
    kind: str
    position: np.ndarray
    molecular: np.ndarray


@dataclass(frozen=True, eq=False)
class DendritePoint:
    receiver: int
    position: np.ndarray


@dataclass(frozen=True, eq=False)
class AxonBranch:
    sender: int
    branch_index: int
    points: np.ndarray


@dataclass(frozen=True)
class Synapse:
    sender: int
    receiver: int
    weight: float
    x: float
    y: float
    path_length: float


@dataclass(frozen=True, eq=False)
class DevelopmentResult:
    seed: int
    arm: Arm
    senders: tuple[Neuron, ...]
    receivers: tuple[Neuron, ...]
    dendrite_points: tuple[DendritePoint, ...]
    branches: tuple[AxonBranch, ...]
    synapses: tuple[Synapse, ...]
    receptor_assignment: tuple[tuple[float, float], ...]
    ligand_assignment: tuple[tuple[float, float], ...]


@dataclass
class _Tip:
    sender: int
    branch_index: int
    heading: float
    points: list[np.ndarray]
    cumulative_length: float
    alive: bool = True


_TURN_ANGLES = np.deg2rad(np.asarray((-60.0, -30.0, 0.0, 30.0, 60.0)))


def _strip_positions(count: int, x: float) -> np.ndarray:
    ys = np.linspace(0.12, 0.88, count, dtype=float)
    return np.column_stack([np.full(count, x, dtype=float), ys])


def _receiver_ligands(config: DevelopmentConfig) -> np.ndarray:
    ys = _strip_positions(config.n_receivers, 0.88)[:, 1]
    return np.column_stack([np.full(config.n_receivers, config.target_x), ys])


def _sender_receptors(config: DevelopmentConfig) -> np.ndarray:
    sender_y = _strip_positions(config.n_senders, 0.08)[:, 1]
    if config.n_senders == config.n_receivers:
        target_y = sender_y
    else:
        q = np.linspace(0.0, 1.0, config.n_senders)
        target_y = 0.12 + 0.76 * q
    return np.column_stack([np.full(config.n_senders, config.target_x), target_y])


def _dendrite_cloud(receiver_positions: np.ndarray) -> tuple[DendritePoint, ...]:
    offsets = np.asarray(
        [
            (-0.10, 0.0),
            (-0.13, -0.025),
            (-0.13, 0.025),
            (-0.16, -0.045),
            (-0.16, 0.045),
            (-0.07, -0.018),
            (-0.07, 0.018),
        ],
        dtype=float,
    )
    points: list[DendritePoint] = []
    for receiver, soma in enumerate(receiver_positions):
        for offset in offsets:
            point = np.clip(soma + offset, 0.0, 1.0)
            points.append(DendritePoint(receiver=receiver, position=point))
    return tuple(points)


def make_world(
    seed: int,
    config: DevelopmentConfig | None = None,
    *,
    arm: Arm = "guided",
) -> tuple[tuple[Neuron, ...], tuple[Neuron, ...], tuple[DendritePoint, ...]]:
    """Create matched soma/dendrite geometry and arm-specific sender labels."""
    del seed
    cfg = config or DevelopmentConfig()
    if arm not in ("guided", "shuffled_labels", "random_walk"):
        raise ValueError(f"unknown developmental arm: {arm}")

    sender_positions = _strip_positions(cfg.n_senders, 0.08)
    receiver_positions = _strip_positions(cfg.n_receivers, 0.88)
    receptors = _sender_receptors(cfg)
    ligands = _receiver_ligands(cfg)

    senders = tuple(
        Neuron(index=i, kind="sender", position=sender_positions[i], molecular=receptors[i])
        for i in range(cfg.n_senders)
    )
    receivers = tuple(
        Neuron(index=i, kind="receiver", position=receiver_positions[i], molecular=ligands[i])
        for i in range(cfg.n_receivers)
    )
    return senders, receivers, _dendrite_cloud(receiver_positions)


def _compatibility(receptor: np.ndarray, ligand: np.ndarray, sigma: float) -> float:
    delta = receptor - ligand
    return float(math.exp(-float(delta @ delta) / (2.0 * sigma * sigma)))


def _crowding(point: np.ndarray, occupied: list[np.ndarray], radius: float) -> float:
    if not occupied:
        return 0.0
    pts = np.asarray(occupied, dtype=float)
    d2 = np.sum((pts - point) ** 2, axis=1)
    return float(np.max(np.exp(-d2 / (2.0 * radius * radius))))


def _candidate_step(
    tip: _Tip,
    receptor: np.ndarray,
    occupied: list[np.ndarray],
    rng: np.random.Generator,
    config: DevelopmentConfig,
    *,
    chemo_enabled: bool,
) -> tuple[np.ndarray, float] | None:
    current = tip.points[-1]
    current_distance = float(np.linalg.norm(receptor - current))
    best: tuple[float, np.ndarray, float] | None = None

    for turn in _TURN_ANGLES:
        heading = tip.heading + float(turn)
        candidate = current + config.step_size * np.asarray(
            [math.cos(heading), math.sin(heading)], dtype=float
        )
        if np.any(candidate < 0.0) or np.any(candidate > 1.0):
            continue
        next_distance = float(np.linalg.norm(receptor - candidate))
        improvement = current_distance - next_distance if chemo_enabled else 0.0
        persistence = math.cos(float(turn))
        crowding = _crowding(candidate, occupied, config.crowding_radius)
        score = (
            config.chemo_weight * improvement
            + config.persistence_weight * persistence
            - config.crowding_weight * crowding
            + config.noise_weight * float(rng.normal())
        )
        if best is None or score > best[0]:
            best = (score, candidate, heading)

    if best is None:
        return None
    return best[1], best[2]


def _capture_synapses(
    sender: int,
    point: np.ndarray,
    path_length: float,
    receptor: np.ndarray,
    receivers: tuple[Neuron, ...],
    dendrites: tuple[DendritePoint, ...],
    existing_pairs: set[tuple[int, int]],
    config: DevelopmentConfig,
) -> list[Synapse]:
    nearest: dict[int, float] = {}
    for dendrite in dendrites:
        if (sender, dendrite.receiver) in existing_pairs:
            continue
        distance = float(np.linalg.norm(point - dendrite.position))
        if distance <= config.capture_radius:
            nearest[dendrite.receiver] = min(distance, nearest.get(dendrite.receiver, math.inf))

    created: list[Synapse] = []
    for receiver in sorted(nearest):
        weight = _compatibility(receptor, receivers[receiver].molecular, config.compatibility_sigma)
        if weight < config.compatibility_threshold:
            continue
        existing_pairs.add((sender, receiver))
        created.append(
            Synapse(
                sender=sender,
                receiver=receiver,
                weight=weight,
                x=float(point[0]),
                y=float(point[1]),
                path_length=float(path_length),
            )
        )
    return created


def develop(
    seed: int = 0,
    arm: Arm = "guided",
    config: DevelopmentConfig | None = None,
) -> DevelopmentResult:
    """Grow branching axons into fixed dendrites and return the frozen anatomy."""
    cfg = config or DevelopmentConfig()
    if arm not in ("guided", "shuffled_labels", "random_walk"):
        raise ValueError(f"unknown developmental arm: {arm}")

    base_senders, receivers, dendrites = make_world(seed, cfg, arm=arm)
    growth_rng = np.random.default_rng(np.random.SeedSequence([seed, 9107]))
    label_rng = np.random.default_rng(np.random.SeedSequence([seed, 9106]))

    receptor_values = np.asarray([n.molecular for n in base_senders], dtype=float)
    if arm == "shuffled_labels" and len(receptor_values) > 1:
        permutation = label_rng.permutation(len(receptor_values))
        if np.array_equal(permutation, np.arange(len(receptor_values))):
            permutation = np.roll(permutation, 1)
        receptor_values = receptor_values[permutation]

    senders = tuple(
        Neuron(
            index=n.index,
            kind=n.kind,
            position=n.position.copy(),
            molecular=receptor_values[n.index].copy(),
        )
        for n in base_senders
    )

    tips: list[_Tip] = []
    branch_counts = np.zeros(cfg.n_senders, dtype=int)
    occupied: list[np.ndarray] = []
    next_branch_index = 0
    for sender in senders:
        start = sender.position.copy()
        tips.append(
            _Tip(
                sender=sender.index,
                branch_index=next_branch_index,
                heading=0.0,
                points=[start],
                cumulative_length=0.0,
            )
        )
        next_branch_index += 1
        occupied.append(start)

    synapses: list[Synapse] = []
    synapse_pairs: set[tuple[int, int]] = set()

    for _ in range(cfg.steps):
        current_tips = list(tips)
        for tip in current_tips:
            if not tip.alive:
                continue
            sender = senders[tip.sender]
            step = _candidate_step(
                tip,
                sender.molecular,
                occupied,
                growth_rng,
                cfg,
                chemo_enabled=arm != "random_walk",
            )
            if step is None:
                tip.alive = False
                continue
            point, heading = step
            tip.points.append(point)
            tip.heading = heading
            tip.cumulative_length += cfg.step_size
            occupied.append(point)
            synapses.extend(
                _capture_synapses(
                    tip.sender,
                    point,
                    tip.cumulative_length,
                    sender.molecular,
                    receivers,
                    dendrites,
                    synapse_pairs,
                    cfg,
                )
            )

            if point[0] >= 0.96:
                tip.alive = False
                continue

            if (
                branch_counts[tip.sender] < cfg.max_branches_per_sender
                and len(tip.points) >= 5
                and growth_rng.random() < cfg.branch_probability
            ):
                direction = -1.0 if growth_rng.random() < 0.5 else 1.0
                child = _Tip(
                    sender=tip.sender,
                    branch_index=next_branch_index,
                    heading=tip.heading + direction * math.radians(42.0),
                    points=[point.copy()],
                    cumulative_length=tip.cumulative_length,
                )
                next_branch_index += 1
                branch_counts[tip.sender] += 1
                tips.append(child)

    branches = tuple(
        AxonBranch(
            sender=tip.sender,
            branch_index=tip.branch_index,
            points=np.asarray(tip.points, dtype=float),
        )
        for tip in sorted(tips, key=lambda item: item.branch_index)
    )
    receptor_assignment = tuple(
        (float(n.molecular[0]), float(n.molecular[1])) for n in senders
    )
    ligand_assignment = tuple(
        (float(n.molecular[0]), float(n.molecular[1])) for n in receivers
    )

    return DevelopmentResult(
        seed=int(seed),
        arm=arm,
        senders=senders,
        receivers=receivers,
        dendrite_points=dendrites,
        branches=branches,
        synapses=tuple(synapses),
        receptor_assignment=receptor_assignment,
        ligand_assignment=ligand_assignment,
    )
