"""Run the GrowingAnttisNeuron v1 developed-cable physical bridge ensemble."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from typing import Iterable

import numpy as np

from growing_anttis_neuron.development import DevelopmentConfig, DevelopmentResult, develop
from growing_anttis_neuron.physical import (
    PassiveCableConfig,
    compile_receiver_cable,
    synapse_physical_metrics,
    whitened_modes,
)

_ARMS = ("guided", "shuffled_labels", "random_walk")
_METRICS = (
    "synapse_count",
    "visible_mode_effective_count",
    "slow_target_decay",
    "next_decay_gap",
    "purification_time_95",
    "soma_transfer_resistance",
)


def _summary(values: Iterable[float | int | None]) -> dict[str, float | int | None]:
    defined = [float(value) for value in values if value is not None]
    if not defined:
        return {
            "defined_count": 0,
            "mean": None,
            "median": None,
            "min": None,
            "max": None,
        }
    data = np.asarray(defined, dtype=float)
    if not np.all(np.isfinite(data)):
        raise FloatingPointError("v1 summary received non-finite values")
    return {
        "defined_count": int(len(data)),
        "mean": float(np.mean(data)),
        "median": float(np.median(data)),
        "min": float(np.min(data)),
        "max": float(np.max(data)),
    }


def _mean_optional(values: Iterable[float | None]) -> float | None:
    defined = [float(value) for value in values if value is not None]
    if not defined:
        return None
    data = np.asarray(defined, dtype=float)
    if not np.all(np.isfinite(data)):
        raise FloatingPointError("v1 per-seed metric became non-finite")
    return float(np.mean(data))


def _sorted_vectors(values: tuple[tuple[float, float], ...]) -> list[list[float]]:
    return [[float(x), float(y)] for x, y in sorted(values)]


def _receiver_cable_physics_exact(left: DevelopmentResult, right: DevelopmentResult) -> bool:
    if len(left.receivers) != len(right.receivers):
        return False
    for receiver in range(len(left.receivers)):
        cable_left = compile_receiver_cable(left, receiver)
        cable_right = compile_receiver_cable(right, receiver)
        if not all(
            np.array_equal(a, b)
            for a, b in (
                (cable_left.positions, cable_right.positions),
                (cable_left.edges, cable_right.edges),
                (cable_left.capacitance, cable_right.capacitance),
                (cable_left.conductance, cable_right.conductance),
                (cable_left.system_matrix, cable_right.system_matrix),
                (whitened_modes(cable_left)[0], whitened_modes(cable_right)[0]),
            )
        ):
            return False
    return True


def _arm_seed_metrics(
    result: DevelopmentResult,
    cable_config: PassiveCableConfig,
) -> dict[str, float | int | None]:
    physical = [
        synapse_physical_metrics(result, synapse, cable_config)
        for synapse in result.synapses
    ]
    return {
        "synapse_count": int(len(result.synapses)),
        "visible_mode_effective_count": _mean_optional(
            item.visible_mode_effective_count for item in physical
        ),
        "slow_target_decay": _mean_optional(item.slow_target_decay for item in physical),
        "next_decay_gap": _mean_optional(item.next_decay_gap for item in physical),
        "purification_time_95": _mean_optional(item.purification_time_95 for item in physical),
        "soma_transfer_resistance": _mean_optional(
            item.soma_transfer_resistance for item in physical
        ),
    }


def _seed_receipt(
    seed: int,
    development_config: DevelopmentConfig,
    cable_config: PassiveCableConfig,
) -> dict:
    results = {
        arm: develop(seed=seed, arm=arm, config=development_config)
        for arm in _ARMS
    }
    guided = results["guided"]
    shuffled = results["shuffled_labels"]

    return {
        "seed": int(seed),
        "controls": {
            "receptor_multiset_exact": (
                _sorted_vectors(guided.receptor_assignment)
                == _sorted_vectors(shuffled.receptor_assignment)
            ),
            "ligand_multiset_exact": (
                _sorted_vectors(guided.ligand_assignment)
                == _sorted_vectors(shuffled.ligand_assignment)
            ),
            "receiver_cable_physics_exact": _receiver_cable_physics_exact(guided, shuffled),
        },
        "arms": {
            arm: {"metrics": _arm_seed_metrics(result, cable_config)}
            for arm, result in results.items()
        },
    }


def run(
    *,
    seeds: Iterable[int],
    development_config: DevelopmentConfig | None = None,
    cable_config: PassiveCableConfig | None = None,
) -> dict:
    """Run matched v1 developmental arms and aggregate physical diagnostics."""
    seed_list = [int(seed) for seed in seeds]
    if not seed_list:
        raise ValueError("at least one seed is required")
    dev_cfg = development_config or DevelopmentConfig()
    cable_cfg = cable_config or PassiveCableConfig()

    per_seed = [
        _seed_receipt(seed, dev_cfg, cable_cfg)
        for seed in seed_list
    ]

    aggregate: dict[str, dict] = {}
    for arm in _ARMS:
        aggregate[arm] = {
            metric: _summary(
                seed_receipt["arms"][arm]["metrics"][metric]
                for seed_receipt in per_seed
            )
            for metric in _METRICS
        }

    paired: dict[str, dict] = {}
    for metric in _METRICS:
        deltas: list[float | None] = []
        for seed_receipt in per_seed:
            guided = seed_receipt["arms"]["guided"]["metrics"][metric]
            shuffled = seed_receipt["arms"]["shuffled_labels"]["metrics"][metric]
            if guided is None or shuffled is None:
                deltas.append(None)
            else:
                deltas.append(float(guided) - float(shuffled))
        paired[metric] = _summary(deltas)
    aggregate["paired_guided_minus_shuffled"] = paired

    return {
        "version": "v1",
        "question": (
            "when v0 developed synapses are compiled as input ports onto identical passive "
            "receiver cables, does intact positional guidance change physical-mode visibility "
            "or passive purification cost relative to exact receptor-label shuffling?"
        ),
        "seeds": seed_list,
        "development_config": asdict(dev_cfg),
        "cable_config": asdict(cable_cfg),
        "aggregate": aggregate,
        "per_seed": per_seed,
        "interpretation": (
            "input-placement physical diagnostics only; guided and shuffled receiver cable "
            "physics must be identical and no preferred scientific sign is required"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=16, help="use integer seeds 0..N-1")
    parser.add_argument("--out", type=Path, default=Path("results/v1.json"))
    args = parser.parse_args()
    if args.seeds < 1:
        raise SystemExit("--seeds must be positive")

    receipt = run(seeds=range(args.seeds))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    paired = receipt["aggregate"]["paired_guided_minus_shuffled"]
    print(json.dumps({"out": str(args.out), "seeds": args.seeds, "paired": paired}, sort_keys=True))


if __name__ == "__main__":
    main()
