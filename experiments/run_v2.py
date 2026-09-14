"""Run GrowingAnttisNeuron v2: one grown anatomy, two operator codebooks.

v2 is an oracle/calibration experiment.  Development grows one guided anatomy per
seed.  The intact arm maps receiver addresses to four passive dendrite/operator
phenotypes; the control shuffles the exact same phenotype multiset across those
same receiver addresses.  Axons, contacts, synapse weights, and molecular growth
history are therefore shared exactly between arms.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import numpy as np

from growing_anttis_neuron.development import DevelopmentResult, Synapse, develop
from growing_anttis_neuron.operator_codebook import (
    PHENOTYPE_SCALES,
    cable_config_for_phenotype,
    intact_assignment,
    normalized_operator_distance,
    shuffled_assignment,
)
from growing_anttis_neuron.physical import (
    PassiveCableConfig,
    ReceiverCable,
    compile_receiver_cable,
    synapse_physical_metrics,
)

_ARMS = ("coded_operator", "shuffled_operator")
_METRICS = (
    "synapse_count",
    "phenotype_match_fraction",
    "operator_target_error",
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
        raise FloatingPointError("v2 summary received non-finite values")
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
        raise FloatingPointError("v2 per-seed metric became non-finite")
    return float(np.mean(data))


def _desired_phenotype(synapse: Synapse) -> int:
    # v0's guided map is topographic: sender address i is paired with receiver
    # address i.  The v2 codebook asks whether that same discrete address can
    # also stand in for a receiver-operator family.
    return int(synapse.sender) % len(PHENOTYPE_SCALES)


def _cable_cache(
    anatomy: DevelopmentResult,
    assignment: tuple[int, ...],
    base_config: PassiveCableConfig,
) -> dict[tuple[int, int], ReceiverCable]:
    cache: dict[tuple[int, int], ReceiverCable] = {}
    for receiver, phenotype in enumerate(assignment):
        key = (receiver, phenotype)
        cache[key] = compile_receiver_cable(
            anatomy,
            receiver,
            cable_config_for_phenotype(phenotype, base_config),
        )
    return cache


def _arm_seed_metrics(
    anatomy: DevelopmentResult,
    assignment: tuple[int, ...],
    *,
    base_config: PassiveCableConfig,
) -> dict[str, float | int | None]:
    if len(assignment) != len(anatomy.receivers):
        raise ValueError("phenotype assignment must cover every receiver")

    actual_cache = _cable_cache(anatomy, assignment, base_config)
    target_cache: dict[tuple[int, int], ReceiverCable] = {}

    matches: list[float] = []
    operator_errors: list[float] = []
    visible_counts: list[float | None] = []
    slow_decays: list[float | None] = []
    decay_gaps: list[float | None] = []
    purification_times: list[float | None] = []
    soma_transfers: list[float | None] = []

    for synapse in anatomy.synapses:
        receiver = int(synapse.receiver)
        actual_phenotype = int(assignment[receiver])
        desired_phenotype = _desired_phenotype(synapse)
        matches.append(float(actual_phenotype == desired_phenotype))

        actual_cable = actual_cache[(receiver, actual_phenotype)]
        target_key = (receiver, desired_phenotype)
        if target_key not in target_cache:
            target_cache[target_key] = compile_receiver_cable(
                anatomy,
                receiver,
                cable_config_for_phenotype(desired_phenotype, base_config),
            )
        operator_errors.append(
            normalized_operator_distance(actual_cable, target_cache[target_key])
        )

        physical = synapse_physical_metrics(
            anatomy,
            synapse,
            cable_config_for_phenotype(actual_phenotype, base_config),
        )
        visible_counts.append(physical.visible_mode_effective_count)
        slow_decays.append(physical.slow_target_decay)
        decay_gaps.append(physical.next_decay_gap)
        purification_times.append(physical.purification_time_95)
        soma_transfers.append(physical.soma_transfer_resistance)

    count = len(anatomy.synapses)
    return {
        "synapse_count": int(count),
        "phenotype_match_fraction": float(np.mean(matches)) if matches else None,
        "operator_target_error": float(np.mean(operator_errors)) if operator_errors else None,
        "visible_mode_effective_count": _mean_optional(visible_counts),
        "slow_target_decay": _mean_optional(slow_decays),
        "next_decay_gap": _mean_optional(decay_gaps),
        "purification_time_95": _mean_optional(purification_times),
        "soma_transfer_resistance": _mean_optional(soma_transfers),
    }


def _seed_receipt(seed: int, base_config: PassiveCableConfig) -> dict:
    anatomy = develop(seed=seed, arm="guided")
    n_receivers = len(anatomy.receivers)
    coded = intact_assignment(n_receivers)
    shuffled = shuffled_assignment(n_receivers, seed=seed)

    assignments = {
        "coded_operator": coded,
        "shuffled_operator": shuffled,
    }
    arms = {
        arm: {
            "metrics": _arm_seed_metrics(
                anatomy,
                assignment,
                base_config=base_config,
            )
        }
        for arm, assignment in assignments.items()
    }

    return {
        "seed": int(seed),
        "controls": {
            # There is intentionally only one development call per seed.  These
            # flags make that matched-design invariant explicit in the receipt.
            "same_developed_anatomy_exact": True,
            "same_synapses_exact": True,
            "phenotype_multiset_exact": sorted(coded) == sorted(shuffled),
        },
        "assignments": {
            arm: [int(value) for value in assignment]
            for arm, assignment in assignments.items()
        },
        "arms": arms,
    }


def run(
    *,
    seeds: Iterable[int],
    base_config: PassiveCableConfig | None = None,
) -> dict:
    """Run the matched v2 operator-codebook calibration ensemble."""
    seed_list = [int(seed) for seed in seeds]
    if not seed_list:
        raise ValueError("at least one seed is required")
    config = base_config or PassiveCableConfig()
    if config.dendrite_scale != 1.0:
        raise ValueError("v2 base_config must leave dendrite_scale at 1.0")

    per_seed = [_seed_receipt(seed, config) for seed in seed_list]

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
            coded_value = seed_receipt["arms"]["coded_operator"]["metrics"][metric]
            shuffled_value = seed_receipt["arms"]["shuffled_operator"]["metrics"][metric]
            if coded_value is None or shuffled_value is None:
                deltas.append(None)
            else:
                deltas.append(float(coded_value) - float(shuffled_value))
        paired[metric] = _summary(deltas)
    aggregate["paired_coded_minus_shuffled"] = paired

    return {
        "version": "v2",
        "question": (
            "when the exact same guided grown anatomy is compiled with a four-entry "
            "developmental address-to-dendrite-operator codebook, does exact phenotype "
            "shuffling break source-to-receiver operator compatibility?"
        ),
        "seeds": seed_list,
        "phenotype_scales": [float(value) for value in PHENOTYPE_SCALES],
        "aggregate": aggregate,
        "per_seed": per_seed,
        "interpretation": (
            "oracle/calibration only: phenotype ids select dendrite-length scales; the "
            "experiment does not claim molecules encode eigenmodes and contains no "
            "activity refinement, evolution, spiking code, or self-differentiation"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=16, help="use integer seeds 0..N-1")
    parser.add_argument("--out", type=Path, default=Path("results/v2.json"))
    args = parser.parse_args()
    if args.seeds < 1:
        raise SystemExit("--seeds must be positive")

    receipt = run(seeds=range(args.seeds))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "out": str(args.out),
                "seeds": args.seeds,
                "aggregate": receipt["aggregate"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
