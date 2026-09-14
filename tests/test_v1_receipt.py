from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from experiments.run_v1 import run
from growing_anttis_neuron.physical import PassiveCableConfig


_METRICS = {
    "synapse_count",
    "visible_mode_effective_count",
    "slow_target_decay",
    "next_decay_gap",
    "purification_time_95",
    "soma_transfer_resistance",
}

# The physical diagnostics use symmetric eigendecompositions and linear solves.
# Different NumPy/LAPACK builds can move the final few floating-point bits while
# leaving the scientific result unchanged.  Keep structure/discrete values exact
# and allow only numerical-roundoff-sized drift in float leaves.
_FLOAT_REL_TOL = 1e-10
_FLOAT_ABS_TOL = 1e-9


def _assert_receipts_close(expected: Any, actual: Any, path: str = "receipt") -> None:
    if isinstance(expected, dict):
        assert isinstance(actual, dict), f"{path}: expected dict, got {type(actual).__name__}"
        assert set(actual) == set(expected), f"{path}: dictionary keys differ"
        for key in expected:
            _assert_receipts_close(expected[key], actual[key], f"{path}.{key}")
        return

    if isinstance(expected, list):
        assert isinstance(actual, list), f"{path}: expected list, got {type(actual).__name__}"
        assert len(actual) == len(expected), f"{path}: list lengths differ"
        for index, (expected_item, actual_item) in enumerate(zip(expected, actual, strict=True)):
            _assert_receipts_close(expected_item, actual_item, f"{path}[{index}]")
        return

    if isinstance(expected, float):
        assert isinstance(actual, float), f"{path}: expected float, got {type(actual).__name__}"
        assert math.isclose(
            expected,
            actual,
            rel_tol=_FLOAT_REL_TOL,
            abs_tol=_FLOAT_ABS_TOL,
        ), f"{path}: {actual!r} != {expected!r} within receipt tolerance"
        return

    assert actual == expected, f"{path}: {actual!r} != {expected!r}"
    assert type(actual) is type(expected), f"{path}: value type differs"


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


def test_v1_rejects_nonhistorical_dendrite_scale() -> None:
    try:
        run(seeds=[0], cable_config=PassiveCableConfig(dendrite_scale=1.2))
    except ValueError as exc:
        assert "dendrite_scale" in str(exc)
    else:
        raise AssertionError("v1 must not hide a nonhistorical dendrite_scale")


def test_receipt_comparison_rejects_scientific_scale_float_changes() -> None:
    expected = {"metric": 0.003016015052863261, "count": 8, "control": True}
    changed = {"metric": expected["metric"] + 1e-4, "count": 8, "control": True}

    try:
        _assert_receipts_close(expected, changed)
    except AssertionError:
        pass
    else:
        raise AssertionError("receipt comparison must reject non-roundoff metric changes")


def test_frozen_v1_receipt_matches_canonical_run() -> None:
    frozen = json.loads(Path("results/v1.json").read_text(encoding="utf-8"))
    _assert_receipts_close(frozen, run(seeds=range(16)))
