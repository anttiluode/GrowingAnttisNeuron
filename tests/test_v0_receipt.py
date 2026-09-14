from __future__ import annotations

import json
from pathlib import Path

from experiments.run_v0 import run


def test_v0_ensemble_contains_all_arms_and_seeds() -> None:
    receipt = run(seeds=[0, 1, 2])

    assert receipt["version"] == "v0"
    assert receipt["seeds"] == [0, 1, 2]
    assert set(receipt["aggregate"]) == {"guided", "shuffled_labels", "random_walk", "paired_guided_minus_shuffled"}
    assert len(receipt["per_seed"]) == 3


def test_v0_aggregate_is_deterministic() -> None:
    first = run(seeds=[0, 1])
    second = run(seeds=[0, 1])

    assert first == second


def test_frozen_v0_receipt_matches_canonical_run() -> None:
    frozen = json.loads(Path("results/v0.json").read_text(encoding="utf-8"))
    assert frozen == run(seeds=list(range(16)))
