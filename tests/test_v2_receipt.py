from __future__ import annotations

from experiments.run_v2 import run


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
