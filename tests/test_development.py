from __future__ import annotations

import numpy as np

from growing_anttis_neuron.development import DevelopmentConfig, develop


def _signature(result) -> tuple:
    branch_points = tuple(
        (branch.sender, tuple((round(float(x), 12), round(float(y), 12)) for x, y in branch.points))
        for branch in result.branches
    )
    synapses = tuple(
        (s.sender, s.receiver, round(float(s.weight), 12), round(float(s.path_length), 12))
        for s in result.synapses
    )
    return branch_points, synapses


def test_development_is_deterministic_for_seed_and_arm() -> None:
    config = DevelopmentConfig(n_senders=6, n_receivers=6, steps=36)
    first = develop(seed=7, arm="guided", config=config)
    second = develop(seed=7, arm="guided", config=config)

    assert _signature(first) == _signature(second)


def test_world_contains_requested_cell_counts() -> None:
    config = DevelopmentConfig(n_senders=5, n_receivers=7, steps=24)
    result = develop(seed=3, arm="guided", config=config)

    assert len(result.senders) == 5
    assert len(result.receivers) == 7
    assert len({p.receiver for p in result.dendrite_points}) == 7


def test_all_axon_points_stay_inside_unit_square() -> None:
    result = develop(seed=11, arm="guided", config=DevelopmentConfig(steps=48))

    points = np.vstack([branch.points for branch in result.branches])
    assert np.all(points >= 0.0)
    assert np.all(points <= 1.0)


def test_synapse_pairs_are_unique_and_valid() -> None:
    config = DevelopmentConfig(n_senders=8, n_receivers=8, steps=52)
    result = develop(seed=13, arm="guided", config=config)

    pairs = [(s.sender, s.receiver) for s in result.synapses]
    assert len(pairs) == len(set(pairs))
    assert all(0 <= sender < config.n_senders for sender, _ in pairs)
    assert all(0 <= receiver < config.n_receivers for _, receiver in pairs)


def test_guided_growth_is_nontrivial() -> None:
    config = DevelopmentConfig(n_senders=8, n_receivers=8, steps=56)
    result = develop(seed=5, arm="guided", config=config)

    assert len(result.branches) >= config.n_senders
    assert sum(len(branch.points) - 1 for branch in result.branches) >= config.n_senders * 3
    assert len(result.synapses) > 0
