"""Frozen connectivity and operator diagnostics for developed organisms."""
from __future__ import annotations

import math

import numpy as np

from .development import DevelopmentConfig, DevelopmentResult, develop


def connectivity_matrix(result: DevelopmentResult) -> np.ndarray:
    """Return sender-by-receiver synaptic weight matrix."""
    matrix = np.zeros((len(result.senders), len(result.receivers)), dtype=float)
    for synapse in result.synapses:
        matrix[synapse.sender, synapse.receiver] = synapse.weight
    return matrix


def _normalized_connectivity(matrix: np.ndarray) -> np.ndarray:
    normalized = np.asarray(matrix, dtype=float).copy()
    row_sums = np.sum(normalized, axis=1)
    nonzero = row_sums > 0.0
    normalized[nonzero] /= row_sums[nonzero, None]
    return normalized


def _stable_operator(matrix: np.ndarray, *, leak: float = 0.12, coupling: float = 0.08) -> np.ndarray:
    normalized = _normalized_connectivity(matrix)
    n_sender, n_receiver = normalized.shape
    symmetric = np.zeros((n_sender + n_receiver, n_sender + n_receiver), dtype=float)
    symmetric[:n_sender, n_sender:] = normalized
    symmetric[n_sender:, :n_sender] = normalized.T

    if symmetric.size:
        eig = np.linalg.eigvalsh(symmetric)
        scale = float(np.max(np.abs(eig))) if eig.size else 0.0
        if scale > 1e-12:
            symmetric /= scale
    operator = (1.0 - leak) * np.eye(n_sender + n_receiver, dtype=float) + coupling * symmetric
    radius = float(np.max(np.abs(np.linalg.eigvals(operator)))) if operator.size else 0.0
    if not radius < 1.0:
        raise FloatingPointError(f"unstable frozen operator: spectral radius={radius}")
    return operator


def _effective_rank(singular_values: np.ndarray) -> float:
    singular = np.asarray(singular_values, dtype=float)
    total = float(np.sum(singular))
    if total <= 1e-15:
        return 0.0
    probabilities = singular / total
    probabilities = probabilities[probabilities > 0.0]
    entropy = -float(np.sum(probabilities * np.log(probabilities)))
    return float(math.exp(entropy))


def _topographic_error(result: DevelopmentResult) -> float:
    if not result.synapses:
        return 1.0
    sender_y = np.asarray([n.position[1] for n in result.senders], dtype=float)
    receiver_y = np.asarray([n.position[1] for n in result.receivers], dtype=float)
    span = 0.76
    errors = [
        abs(float(sender_y[s.sender] - receiver_y[s.receiver])) / span
        for s in result.synapses
    ]
    return float(np.mean(errors))


def operator_metrics(result: DevelopmentResult) -> dict:
    """Measure geometry and a stable bipartite frozen operator."""
    matrix = connectivity_matrix(result)
    singular = np.linalg.svd(matrix, compute_uv=False)
    operator = _stable_operator(matrix)
    magnitudes = np.sort(np.abs(np.linalg.eigvals(operator)))[::-1]
    slow_gap = float(magnitudes[0] - magnitudes[1]) if len(magnitudes) >= 2 else 0.0
    path_lengths = [s.path_length for s in result.synapses]

    metrics = {
        "connection_count": int(len(result.synapses)),
        "mean_wiring_length": float(np.mean(path_lengths)) if path_lengths else 0.0,
        "topographic_error": _topographic_error(result),
        "singular_values": [float(value) for value in singular],
        "effective_rank": _effective_rank(singular),
        "spectral_radius": float(magnitudes[0]) if magnitudes.size else 0.0,
        "slow_mode_separation": slow_gap,
    }
    if not all(
        math.isfinite(float(metrics[key]))
        for key in (
            "connection_count",
            "mean_wiring_length",
            "topographic_error",
            "effective_rank",
            "spectral_radius",
            "slow_mode_separation",
        )
    ):
        raise FloatingPointError("non-finite developmental operator metric")
    return metrics


def _sorted_vectors(values: tuple[tuple[float, float], ...]) -> list[list[float]]:
    return [[float(x), float(y)] for x, y in sorted(values)]


def receipt_for_seed(seed: int, config: DevelopmentConfig | None = None) -> dict:
    """Run all matched developmental arms and return one deterministic receipt."""
    cfg = config or DevelopmentConfig()
    results = {
        arm: develop(seed=seed, arm=arm, config=cfg)
        for arm in ("guided", "shuffled_labels", "random_walk")
    }
    guided = results["guided"]
    shuffled = results["shuffled_labels"]

    guided_receptors = _sorted_vectors(guided.receptor_assignment)
    shuffled_receptors = _sorted_vectors(shuffled.receptor_assignment)
    guided_ligands = _sorted_vectors(guided.ligand_assignment)
    shuffled_ligands = _sorted_vectors(shuffled.ligand_assignment)

    return {
        "seed": int(seed),
        "config": {
            "n_senders": cfg.n_senders,
            "n_receivers": cfg.n_receivers,
            "steps": cfg.steps,
            "step_size": cfg.step_size,
            "capture_radius": cfg.capture_radius,
            "compatibility_sigma": cfg.compatibility_sigma,
            "compatibility_threshold": cfg.compatibility_threshold,
            "branch_probability": cfg.branch_probability,
            "max_branches_per_sender": cfg.max_branches_per_sender,
        },
        "controls": {
            "receptor_multiset_exact": guided_receptors == shuffled_receptors,
            "ligand_multiset_exact": guided_ligands == shuffled_ligands,
            "guided_receptors": guided_receptors,
            "shuffled_receptors": shuffled_receptors,
        },
        "arms": {
            arm: {
                "metrics": operator_metrics(result),
                "synapses": [
                    {
                        "sender": s.sender,
                        "receiver": s.receiver,
                        "weight": s.weight,
                        "path_length": s.path_length,
                    }
                    for s in result.synapses
                ],
                "receptor_assignment": [list(v) for v in result.receptor_assignment],
            }
            for arm, result in results.items()
        },
    }
