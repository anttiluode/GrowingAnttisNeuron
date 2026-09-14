from __future__ import annotations

import json
from pathlib import Path

from experiments.run_v1 import run


_METRICS = {
    "synapse_count",
    "visible_mode_effective_count",
    "slow_target_decay",
    "next_decay_gap",
    "purification_time_95",
    "soma_transfer_resistance",
}


def test_v1_receipt_contains_matched_arms_and_physical_metrics() -> None:
    receipt = run(seeds=[0, 1])

    assert receipt["version"] == "v1"
    assert receipt["seeds"] == [0, 1]
    assert set(receipt["aggregate"]) == {
        "guided",
        "shuffled_labels",
        "random_walk",
        "paired_guided_minus_shuffled",
    }
    assert len(receipt["per_seed"]) == 2

    for arm in ("guided", "shuffled_labels", "random_walk"):
        assert set(receipt["aggregate"][arm]) == _METRICS
        for metric in _METRICS:
            summary = receipt["aggregate"][arm][metric]
            assert set(summary) == {"defined_count", "mean", "median", "min", "max"}
            assert 0 <= summary["defined_count"] <= 2


def test_v1_receipt_records_exact_developmental_controls() -> None:
    receipt = run(seeds=[2])
    controls = receipt["per_seed"][0]["controls"]

    assert controls["receptor_multiset_exact"] is True
    assert controls["ligand_multiset_exact"] is True
    assert controls["receiver_cable_physics_exact"] is True


def test_v1_receipt_is_exactly_deterministic() -> None:
    first = run(seeds=[0, 1])
    second = run(seeds=[0, 1])

    assert first == second


def test_v1_rejects_empty_seed_ensemble() -> None:
    try:
        run(seeds=[])
    except ValueError as exc:
        assert "seed" in str(exc).lower()
    else:
        raise AssertionError("empty v1 ensemble must be rejected")


def test_frozen_v1_receipt_matches_canonical_run() -> None:
    frozen = json.loads(Path("results/v1.json").read_text(encoding="utf-8"))
    assert frozen == run(seeds=range(16))
