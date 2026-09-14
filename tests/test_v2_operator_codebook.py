from __future__ import annotations

import numpy as np

from growing_anttis_neuron.development import develop
from growing_anttis_neuron.operator_codebook import (
    PHENOTYPE_SCALES,
    cable_config_for_phenotype,
    intact_assignment,
    normalized_operator_distance,
    shuffled_assignment,
)
from growing_anttis_neuron.physical import PassiveCableConfig, compile_receiver_cable, whitened_modes


def test_dendrite_scale_changes_geometry_and_passive_operator() -> None:
    anatomy = develop(seed=0, arm="guided")
    short_cfg = PassiveCableConfig(dendrite_scale=0.70)
    long_cfg = PassiveCableConfig(dendrite_scale=1.45)

    short = compile_receiver_cable(anatomy, receiver=0, config=short_cfg)
    long = compile_receiver_cable(anatomy, receiver=0, config=long_cfg)

    assert np.array_equal(short.positions[0], long.positions[0])
    assert short.positions.shape == long.positions.shape
    short_offsets = short.positions[1:] - short.positions[0]
    long_offsets = long.positions[1:] - long.positions[0]
    assert np.allclose(long_offsets, short_offsets * (1.45 / 0.70), rtol=0.0, atol=1e-14)

    short_decay, _ = whitened_modes(short)
    long_decay, _ = whitened_modes(long)
    assert not np.allclose(short_decay, long_decay, rtol=1e-7, atol=1e-10)
    assert not np.allclose(short.system_matrix, long.system_matrix, rtol=1e-7, atol=1e-12)


def test_operator_codebook_has_four_distinct_physical_phenotypes() -> None:
    assert PHENOTYPE_SCALES == (0.70, 0.90, 1.20, 1.45)
    anatomy = develop(seed=0, arm="guided")
    cables = [
        compile_receiver_cable(anatomy, 0, cable_config_for_phenotype(index))
        for index in range(4)
    ]
    for left in range(4):
        assert normalized_operator_distance(cables[left], cables[left]) == 0.0
        for right in range(left + 1, 4):
            assert normalized_operator_distance(cables[left], cables[right]) > 1e-3


def test_shuffled_codebook_preserves_exact_multiset_but_breaks_address_relation() -> None:
    intact = intact_assignment(8)
    shuffled = shuffled_assignment(8, seed=7)

    assert intact == (0, 1, 2, 3, 0, 1, 2, 3)
    assert shuffled == shuffled_assignment(8, seed=7)
    assert sorted(shuffled) == sorted(intact)
    assert shuffled != intact
    assert all(0 <= phenotype < len(PHENOTYPE_SCALES) for phenotype in shuffled)
