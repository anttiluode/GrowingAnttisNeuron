"""Developmental addresses as a tiny codebook for passive operator families.

v2 is deliberately an oracle/calibration layer: a phenotype id selects a
dendrite-length scale, and the shuffled control preserves the exact phenotype
multiset while breaking its receiver-address relation.  Molecules are not
claimed to encode eigenmodes directly.
"""
from __future__ import annotations

from dataclasses import replace
import math

import numpy as np

from .physical import PassiveCableConfig, ReceiverCable


PHENOTYPE_SCALES: tuple[float, ...] = (0.70, 0.90, 1.20, 1.45)
_SHUFFLE_STREAM = 0x0A17C0DE


def intact_assignment(n_receivers: int) -> tuple[int, ...]:
    """Repeat the four-entry developmental codebook across receiver addresses."""
    if isinstance(n_receivers, bool) or not isinstance(n_receivers, int) or n_receivers < 1:
        raise ValueError("n_receivers must be a positive integer")
    return tuple(index % len(PHENOTYPE_SCALES) for index in range(n_receivers))


def shuffled_assignment(n_receivers: int, *, seed: int) -> tuple[int, ...]:
    """Break address→phenotype correspondence without changing the phenotype multiset."""
    base = np.asarray(intact_assignment(n_receivers), dtype=int)
    rng = np.random.default_rng(np.random.SeedSequence([int(seed), _SHUFFLE_STREAM]))
    candidate = base[rng.permutation(n_receivers)]
    if n_receivers > 1 and len(set(base.tolist())) > 1 and np.array_equal(candidate, base):
        candidate = np.roll(base, 1)
    return tuple(int(value) for value in candidate)


def cable_config_for_phenotype(
    phenotype: int,
    base: PassiveCableConfig | None = None,
) -> PassiveCableConfig:
    """Compile one developmental phenotype into a passive cable configuration."""
    if isinstance(phenotype, bool) or not isinstance(phenotype, int):
        raise ValueError("phenotype must be an integer index")
    if phenotype < 0 or phenotype >= len(PHENOTYPE_SCALES):
        raise ValueError("phenotype index outside codebook")
    return replace(
        base or PassiveCableConfig(),
        dendrite_scale=PHENOTYPE_SCALES[phenotype],
    )


def _whitened_operator(cable: ReceiverCable) -> np.ndarray:
    capacitance = np.asarray(cable.capacitance, dtype=float)
    system = np.asarray(cable.system_matrix, dtype=float)
    if capacitance.ndim != 1 or system.shape != (len(capacitance), len(capacitance)):
        raise ValueError("incompatible cable matrices")
    if np.any(capacitance <= 0.0) or not np.all(np.isfinite(capacitance)):
        raise ValueError("capacitance must be finite and positive")
    inv_sqrt = np.diag(1.0 / np.sqrt(capacitance))
    operator = inv_sqrt @ system @ inv_sqrt
    return 0.5 * (operator + operator.T)


def normalized_operator_distance(actual: ReceiverCable, target: ReceiverCable) -> float:
    """Normalized Frobenius distance in the common compartment coordinate system."""
    left = _whitened_operator(actual)
    right = _whitened_operator(target)
    if left.shape != right.shape:
        raise ValueError("operator distance requires matched compartment dimensions")
    denominator = float(np.linalg.norm(right, ord="fro"))
    if not math.isfinite(denominator) or denominator <= 0.0:
        raise ValueError("target operator norm must be finite and positive")
    distance = float(np.linalg.norm(left - right, ord="fro") / denominator)
    if not math.isfinite(distance):
        raise FloatingPointError("operator distance became non-finite")
    return distance
