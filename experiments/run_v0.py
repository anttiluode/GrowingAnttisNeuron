"""Run the matched developmental v0 ensemble and emit a deterministic receipt."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import numpy as np

from growing_anttis_neuron.development import DevelopmentConfig
from growing_anttis_neuron.operator import receipt_for_seed

_ARMS = ("guided", "shuffled_labels", "random_walk")
_METRICS = (
    "connection_count",
    "mean_wiring_length",
    "topographic_error",
    "effective_rank",
    "spectral_radius",
    "slow_mode_separation",
)


def _summary(values: list[float]) -> dict[str, float]:
    data = np.asarray(values, dtype=float)
    return {
        "mean": float(np.mean(data)),
        "median": float(np.median(data)),
        "min": float(np.min(data)),
        "max": float(np.max(data)),
    }


def run(
    *,
    seeds: Iterable[int],
    config: DevelopmentConfig | None = None,
) -> dict:
    """Run matched arms for the supplied seeds and aggregate without sign gates."""
    seed_list = [int(seed) for seed in seeds]
    if not seed_list:
        raise ValueError("at least one seed is required")
    cfg = config or DevelopmentConfig()
    per_seed = [receipt_for_seed(seed, cfg) for seed in seed_list]

    aggregate: dict[str, dict] = {}
    for arm in _ARMS:
        aggregate[arm] = {
            metric: _summary(
                [float(seed_receipt["arms"][arm]["metrics"][metric]) for seed_receipt in per_seed]
            )
            for metric in _METRICS
        }

    paired: dict[str, dict[str, float]] = {}
    for metric in _METRICS:
        deltas = [
            float(seed_receipt["arms"]["guided"]["metrics"][metric])
            - float(seed_receipt["arms"]["shuffled_labels"]["metrics"][metric])
            for seed_receipt in per_seed
        ]
        paired[metric] = _summary(deltas)
    aggregate["paired_guided_minus_shuffled"] = paired

    return {
        "version": "v0",
        "question": (
            "does intact chemoaffinity-style positional matching grow a different frozen "
            "operator than an exact receptor-label shuffle or unguided random walk?"
        ),
        "seeds": seed_list,
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
            "chemo_weight": cfg.chemo_weight,
            "persistence_weight": cfg.persistence_weight,
            "crowding_weight": cfg.crowding_weight,
            "noise_weight": cfg.noise_weight,
        },
        "aggregate": aggregate,
        "per_seed": per_seed,
        "interpretation": (
            "developmental/operator diagnostics only; scientific deltas are recorded with "
            "their sign and are never required positive by CI"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=16, help="use integer seeds 0..N-1")
    parser.add_argument("--out", type=Path, default=Path("results/v0.json"))
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
