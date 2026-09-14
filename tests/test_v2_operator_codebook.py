from __future__ import annotations

import numpy as np

from growing_anttis_neuron.development import develop
from growing_anttis_neuron.physical import PassiveCableConfig, compile_receiver_cable, whitened_modes


def test_dendrite_scale_changes_geometry_and_passive_operator() -> None:
    anatomy = develop(seed=0, arm="guided")
    short_cfg = PassiveCableConfig(dendrite_scale=0.70)
    long_cfg = PassiveCableConfig(dendrite_scale=1.45)

    short = compile_receiver_cable(anatomy, receiver=0, config=short_cfg)
    long = compile_receiver_cable(anatomy, receiver=0, config=long_cfg)

    # Phenotype changes the dendrite, not the soma or compartment identity.
    assert np.array_equal(short.positions[0], long.positions[0])
    assert short.positions.shape == long.positions.shape
    short_offsets = short.positions[1:] - short.positions[0]
    long_offsets = long.positions[1:] - long.positions[0]
    assert np.allclose(long_offsets, short_offsets * (1.45 / 0.70), rtol=0.0, atol=1e-14)

    # The resulting physical operator must genuinely differ.
    short_decay, _ = whitened_modes(short)
    long_decay, _ = whitened_modes(long)
    assert not np.allclose(short_decay, long_decay, rtol=1e-7, atol=1e-10)
    assert not np.allclose(short.system_matrix, long.system_matrix, rtol=1e-7, atol=1e-12)
