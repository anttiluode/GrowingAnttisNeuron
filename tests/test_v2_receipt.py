from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from experiments.run_v2 import run


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


def test_v2_reuses_one_anatomy_and_only_shuffles_operator_codebook() -> None:
    receipt = run(seeds=[0, 1])

    assert receipt["version"] == "v2"
    assert receipt["seeds"] == [0, 1]
    assert set(receipt["aggregate"]) == {
        "coded_operator",
        "shuffled_operator",
        "paired_coded_minus_shuffled",
    }

    for seed_receipt in receipt["per_seed"]:
        controls = seed_receipt["controls"]
        assert controls["same_developed_anatomy_exact"] is True
        assert controls["same_synapses_exact"] is True
        assert controls["phenotype_multiset_exact"] is True
        assert seed_receipt["assignments"]["coded_operator"] != seed_receipt["assignments"]["shuffled_operator"]

        coded = seed_receipt["arms"]["coded_operator"]["metrics"]
        assert coded["phenotype_match_fraction"] == 1.0
        assert abs(coded["operator_target_error"]) < 1e-14


def test_v2_is_deterministic() -> None:
    assert run(seeds=[2]) == run(seeds=[2])


def test_frozen_v2_receipt_matches_canonical_run() -> None:
    frozen = json.loads(Path("results/v2.json").read_text(encoding="utf-8"))
    _assert_receipts_close(frozen, run(seeds=range(16)))
