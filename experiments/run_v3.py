"""Run GrowingAnttisNeuron v3: temporal statistics grow passive operators locally."""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict
from functools import lru_cache
import json
from pathlib import Path

import numpy as np

from growing_anttis_neuron.development import develop
from growing_anttis_neuron.homeostasis import (
    HomeostaticGrowthConfig,
    grow_to_local_setpoint,
    local_voltage_rms,
)
from growing_anttis_neuron.physical import (
    PassiveCableConfig,
    ReceiverCable,
    compile_receiver_cable,
    whitened_modes,
)

_CORRELATIONS = (0.0, 0.2, 0.4, 0.6)
_SCALE_GRID = (0.7, 0.85, 1.0, 1.2, 1.5, 1.8, 2.2, 2.6)
_INPUT_VARIANCE = 1.0
_INITIAL_SCALE = 1.0
_RECEIVER = 0
_REPRESENTATIVE_COMPARTMENT = 1


def _whitened_operator(cable: ReceiverCable) -> np.ndarray:
    inv_sqrt = np.diag(1.0 / np.sqrt(np.asarray(cable.capacitance, dtype=float)))
    operator = inv_sqrt @ np.asarray(cable.system_matrix, dtype=float) @ inv_sqrt
    return 0.5 * (operator + operator.T)


def _operator_distance(reference: ReceiverCable, candidate: ReceiverCable) -> float:
    left = _whitened_operator(reference)
    right = _whitened_operator(candidate)
    denominator = max(float(np.linalg.norm(left, ord="fro")), 1e-15)
    return float(np.linalg.norm(right - left, ord="fro") / denominator)


def _strictly_increasing(values: list[float]) -> bool:
    return all(left < right for left, right in zip(values[:-1], values[1:], strict=True))


def _strictly_decreasing(values: list[float]) -> bool:
    return all(left > right for left, right in zip(values[:-1], values[1:], strict=True))


@lru_cache(maxsize=1)
def _canonical_receipt() -> dict:
    result = develop(seed=0, arm="guided")
    cable_cfg = PassiveCableConfig(dendrite_scale=_INITIAL_SCALE)
    base = compile_receiver_cable(result, receiver=_RECEIVER, config=cable_cfg)
    lineage_edges = np.asarray(base.edges, dtype=int)
    growth_cfg = HomeostaticGrowthConfig()

    target_rms = local_voltage_rms(
        result,
        receiver=_RECEIVER,
        compartment=_REPRESENTATIVE_COMPARTMENT,
        rho=0.0,
        input_variance=_INPUT_VARIANCE,
        dendrite_scale=_INITIAL_SCALE,
        lineage_edges=lineage_edges,
        cable_config=cable_cfg,
    )

    trajectories: list[dict] = []
    for rho in _CORRELATIONS:
        grown = grow_to_local_setpoint(
            result,
            receiver=_RECEIVER,
            compartment=_REPRESENTATIVE_COMPARTMENT,
            rho=rho,
            target_rms=target_rms,
            input_variance=_INPUT_VARIANCE,
            initial_scale=_INITIAL_SCALE,
            lineage_edges=lineage_edges,
            config=growth_cfg,
            cable_config=cable_cfg,
        )
        grown_cable = compile_receiver_cable(
            result,
            receiver=_RECEIVER,
            config=PassiveCableConfig(dendrite_scale=grown.final_scale),
            lineage_edges=lineage_edges,
        )
        decays, _ = whitened_modes(grown_cable)
        trajectories.append(
            {
                "rho": float(rho),
                "initial_scale": float(grown.initial_scale),
                "final_scale": float(grown.final_scale),
                "initial_rms": float(grown.initial_rms),
                "final_rms": float(grown.final_rms),
                "target_rms": float(grown.target_rms),
                "steps": int(grown.steps),
                "converged": bool(grown.converged),
                "operator_distance_from_baseline": _operator_distance(base, grown_cable),
                "generalized_decay_spectrum": [float(value) for value in decays],
            }
        )

    temporal_ordering_passed = 0
    scale_monotonic_passed = 0
    temporal_by_compartment: list[dict] = []
    scale_by_compartment: list[dict] = []
    n_compartments = len(base.positions) - 1
    for compartment in range(1, n_compartments + 1):
        temporal_values = [
            local_voltage_rms(
                result,
                receiver=_RECEIVER,
                compartment=compartment,
                rho=rho,
                input_variance=_INPUT_VARIANCE,
                dendrite_scale=_INITIAL_SCALE,
                lineage_edges=lineage_edges,
                cable_config=cable_cfg,
            )
            for rho in _CORRELATIONS
        ]
        temporal_pass = _strictly_increasing(temporal_values)
        temporal_ordering_passed += int(temporal_pass)
        temporal_by_compartment.append(
            {
                "compartment": int(compartment),
                "rms_by_rho": [float(value) for value in temporal_values],
                "passed": bool(temporal_pass),
            }
        )

        for rho in _CORRELATIONS:
            scale_values = [
                local_voltage_rms(
                    result,
                    receiver=_RECEIVER,
                    compartment=compartment,
                    rho=rho,
                    input_variance=_INPUT_VARIANCE,
                    dendrite_scale=scale,
                    lineage_edges=lineage_edges,
                    cable_config=cable_cfg,
                )
                for scale in _SCALE_GRID
            ]
            scale_pass = _strictly_decreasing(scale_values)
            scale_monotonic_passed += int(scale_pass)
            scale_by_compartment.append(
                {
                    "compartment": int(compartment),
                    "rho": float(rho),
                    "rms_by_scale": [float(value) for value in scale_values],
                    "passed": bool(scale_pass),
                }
            )

    return {
        "version": "v3",
        "question": (
            "can equal-power inputs with different temporal correlations make one local voltage "
            "homeostat grow initially identical fixed-lineage dendrites into different passive "
            "operators without phenotype labels, eigenmode targets, reward, or evolution?"
        ),
        "correlations": [float(value) for value in _CORRELATIONS],
        "input_variance": float(_INPUT_VARIANCE),
        "target_rms": float(target_rms),
        "growth_config": asdict(growth_cfg),
        "cable_config": asdict(cable_cfg),
        "receiver": int(_RECEIVER),
        "representative_compartment": int(_REPRESENTATIVE_COMPARTMENT),
        "controls": {
            "same_initial_scale": True,
            "initial_scale": float(_INITIAL_SCALE),
            "same_input_variance": True,
            "fixed_lineage_edges": True,
            "lineage_edges": lineage_edges.tolist(),
            "growth_signal": "local_voltage_rms_only",
            "oracle_fields_used": [],
            "target_source": "rho=0 baseline at scale=1",
        },
        "trajectories": trajectories,
        "robustness": {
            "temporal_ordering_passed": int(temporal_ordering_passed),
            "temporal_ordering_total": int(n_compartments),
            "scale_monotonic_passed": int(scale_monotonic_passed),
            "scale_monotonic_total": int(n_compartments * len(_CORRELATIONS)),
            "scale_grid": [float(value) for value in _SCALE_GRID],
            "temporal_by_compartment": temporal_by_compartment,
            "scale_by_compartment": scale_by_compartment,
        },
        "interpretation": (
            "post-growth operator spectra are diagnostics only; the growth rule sees only local "
            "stationary voltage RMS relative to one shared setpoint, and no task utility is claimed"
        ),
    }


def run() -> dict:
    """Return a defensive copy of the deterministic canonical v3 receipt."""
    return deepcopy(_canonical_receipt())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("results/v3.json"))
    args = parser.parse_args()

    receipt = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "out": str(args.out),
                "target_rms": receipt["target_rms"],
                "final_scales": [item["final_scale"] for item in receipt["trajectories"]],
                "temporal_ordering": [
                    receipt["robustness"]["temporal_ordering_passed"],
                    receipt["robustness"]["temporal_ordering_total"],
                ],
                "scale_monotonic": [
                    receipt["robustness"]["scale_monotonic_passed"],
                    receipt["robustness"]["scale_monotonic_total"],
                ],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
