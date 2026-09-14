"""Local voltage homeostasis for signal-grown passive dendritic operators.

v3 deliberately gives the growth rule no target phenotype, eigenmode, sender id,
or task reward. Equal-variance temporal inputs differ only in autocorrelation;
the local voltage statistic is the sole feedback signal that changes morphology.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import math

import numpy as np

from .development import DevelopmentResult
from .physical import PassiveCableConfig, ReceiverCable, compile_receiver_cable


@dataclass(frozen=True)
class HomeostaticGrowthConfig:
    """Parameters of the one-dimensional local dendritic growth rule."""

    growth_rate: float = 0.25
    min_scale: float = 0.5
    max_scale: float = 4.0
    relative_tolerance: float = 1e-4
    max_steps: int = 200

    def __post_init__(self) -> None:
        positive = (
            self.growth_rate,
            self.min_scale,
            self.max_scale,
            self.relative_tolerance,
        )
        if not all(math.isfinite(value) and value > 0.0 for value in positive):
            raise ValueError("homeostatic growth parameters must be finite and positive")
        if self.min_scale >= self.max_scale:
            raise ValueError("min_scale must be smaller than max_scale")
        if isinstance(self.max_steps, bool) or not isinstance(self.max_steps, int) or self.max_steps < 1:
            raise ValueError("max_steps must be a positive integer")


@dataclass(frozen=True)
class HomeostaticGrowthResult:
    """Receipt for one local signal-driven morphology trajectory."""

    rho: float
    initial_scale: float
    final_scale: float
    initial_rms: float
    final_rms: float
    target_rms: float
    steps: int
    converged: bool


def _validate_signal(rho: float, input_variance: float) -> None:
    if not math.isfinite(rho) or abs(rho) >= 1.0:
        raise ValueError("rho must be finite and lie strictly inside (-1, 1)")
    if not math.isfinite(input_variance) or input_variance <= 0.0:
        raise ValueError("input_variance must be finite and positive")


def stationary_voltage_covariance(
    cable: ReceiverCable,
    *,
    compartment: int,
    rho: float,
    input_variance: float = 1.0,
    dt: float = 0.05,
) -> np.ndarray:
    """Exact stationary voltage covariance for a unit-location AR(1) current.

    The implicit passive step is

        v[t+1] = M v[t] + k u[t]
        u[t+1] = rho u[t] + sqrt((1-rho^2) var(u)) eps[t]

    so the augmented stationary covariance solves a discrete Lyapunov equation.
    The solve uses only the physical forward operator; no modal decomposition is
    available to the growth rule.
    """
    _validate_signal(rho, input_variance)
    if not math.isfinite(dt) or dt <= 0.0:
        raise ValueError("dt must be finite and positive")
    n = len(cable.capacitance)
    if isinstance(compartment, bool) or not isinstance(compartment, int):
        raise ValueError("compartment must be an integer index")
    if compartment < 0 or compartment >= n:
        raise ValueError("compartment outside cable")

    capacitance = np.asarray(cable.capacitance, dtype=float)
    system = np.asarray(cable.system_matrix, dtype=float)
    transition = np.asarray(cable.step_matrix, dtype=float)
    if capacitance.shape != (n,) or system.shape != (n, n) or transition.shape != (n, n):
        raise ValueError("incompatible cable matrices")

    implicit = np.diag(capacitance) + dt * system
    forcing = np.zeros(n, dtype=float)
    forcing[compartment] = 1.0
    input_step = np.linalg.solve(implicit, dt * forcing)

    augmented = np.zeros((n + 1, n + 1), dtype=float)
    augmented[:n, :n] = transition
    augmented[:n, n] = input_step
    augmented[n, n] = rho
    if np.max(np.abs(np.linalg.eigvals(augmented))) >= 1.0:
        raise FloatingPointError("augmented passive/AR(1) system is not stable")

    noise = np.zeros((n + 1, n + 1), dtype=float)
    noise[n, n] = (1.0 - rho * rho) * input_variance
    dimension = n + 1
    lyapunov = np.eye(dimension * dimension) - np.kron(augmented, augmented)
    covariance = np.linalg.solve(
        lyapunov,
        noise.reshape(-1, order="F"),
    ).reshape((dimension, dimension), order="F")
    covariance = 0.5 * (covariance + covariance.T)
    voltage = covariance[:n, :n]
    if not np.all(np.isfinite(voltage)):
        raise FloatingPointError("stationary voltage covariance became non-finite")
    diagonal = np.diag(voltage)
    if np.min(diagonal) < -1e-9:
        raise FloatingPointError("stationary voltage covariance has negative variance")
    return voltage


def local_voltage_rms(
    result: DevelopmentResult,
    *,
    receiver: int,
    compartment: int,
    rho: float,
    input_variance: float = 1.0,
    dendrite_scale: float = 1.0,
    lineage_edges: np.ndarray,
    cable_config: PassiveCableConfig | None = None,
) -> float:
    """Return the stationary local voltage RMS seen by one dendritic compartment."""
    if not math.isfinite(dendrite_scale) or dendrite_scale <= 0.0:
        raise ValueError("dendrite_scale must be finite and positive")
    base = cable_config or PassiveCableConfig()
    cfg = replace(base, dendrite_scale=float(dendrite_scale))
    cable = compile_receiver_cable(
        result,
        receiver,
        cfg,
        lineage_edges=lineage_edges,
    )
    covariance = stationary_voltage_covariance(
        cable,
        compartment=compartment,
        rho=rho,
        input_variance=input_variance,
        dt=cfg.dt,
    )
    variance = max(0.0, float(covariance[compartment, compartment]))
    rms = math.sqrt(variance)
    if not math.isfinite(rms):
        raise FloatingPointError("local voltage RMS became non-finite")
    return rms


def grow_to_local_setpoint(
    result: DevelopmentResult,
    *,
    receiver: int,
    compartment: int,
    rho: float,
    target_rms: float,
    input_variance: float = 1.0,
    initial_scale: float = 1.0,
    lineage_edges: np.ndarray,
    config: HomeostaticGrowthConfig | None = None,
    cable_config: PassiveCableConfig | None = None,
) -> HomeostaticGrowthResult:
    """Grow or shrink one fixed-lineage dendrite using only its local RMS error."""
    _validate_signal(rho, input_variance)
    if not math.isfinite(target_rms) or target_rms <= 0.0:
        raise ValueError("target_rms must be finite and positive")
    if not math.isfinite(initial_scale) or initial_scale <= 0.0:
        raise ValueError("initial_scale must be finite and positive")
    growth = config or HomeostaticGrowthConfig()
    if initial_scale < growth.min_scale or initial_scale > growth.max_scale:
        raise ValueError("initial_scale must lie inside growth bounds")

    def measure(scale: float) -> float:
        return local_voltage_rms(
            result,
            receiver=receiver,
            compartment=compartment,
            rho=rho,
            input_variance=input_variance,
            dendrite_scale=scale,
            lineage_edges=lineage_edges,
            cable_config=cable_config,
        )

    scale = float(initial_scale)
    initial_rms = measure(scale)
    current_rms = initial_rms
    for step in range(growth.max_steps + 1):
        relative_error = current_rms / target_rms - 1.0
        if abs(relative_error) <= growth.relative_tolerance:
            return HomeostaticGrowthResult(
                rho=float(rho),
                initial_scale=float(initial_scale),
                final_scale=float(scale),
                initial_rms=float(initial_rms),
                final_rms=float(current_rms),
                target_rms=float(target_rms),
                steps=int(step),
                converged=True,
            )
        if step == growth.max_steps:
            break
        proposed = scale * math.exp(growth.growth_rate * relative_error)
        scale = float(np.clip(proposed, growth.min_scale, growth.max_scale))
        current_rms = measure(scale)

    return HomeostaticGrowthResult(
        rho=float(rho),
        initial_scale=float(initial_scale),
        final_scale=float(scale),
        initial_rms=float(initial_rms),
        final_rms=float(current_rms),
        target_rms=float(target_rms),
        steps=int(growth.max_steps),
        converged=False,
    )
