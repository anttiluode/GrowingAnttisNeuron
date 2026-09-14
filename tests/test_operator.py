from __future__ import annotations

import math

import numpy as np

from growing_anttis_neuron.development import DevelopmentConfig, develop
from growing_anttis_neuron.operator import connectivity_matrix, operator_metrics, receipt_for_seed


def test_label_shuffle_preserves_exact_molecular_multisets() -> None:
    config = DevelopmentConfig(n_senders=8, n_receivers=8, steps=44)
    guided = develop(seed=17, arm="guided", config=config)
    shuffled = develop(seed=17, arm="shuffled_labels", config=config)

    assert sorted(guided.receptor_assignment) == sorted(shuffled.receptor_assignment)
    assert sorted(guided.ligand_assignment) == sorted(shuffled.ligand_assignment)
    assert guided.receptor_assignment != shuffled.receptor_assignment


def test_label_shuffle_does_not_consume_the_growth_noise_stream() -> None:
    config = DevelopmentConfig(
        n_senders=6,
        n_receivers=6,
        steps=32,
        chemo_weight=0.0,
        branch_probability=0.12,
    )
    guided = develop(seed=21, arm="guided", config=config)
    shuffled = develop(seed=21, arm="shuffled_labels", config=config)

    guided_paths = [np.asarray(branch.points) for branch in guided.branches]
    shuffled_paths = [np.asarray(branch.points) for branch in shuffled.branches]
    assert len(guided_paths) == len(shuffled_paths)
    for left, right in zip(guided_paths, shuffled_paths):
        assert np.array_equal(left, right)


def test_connectivity_matrix_has_sender_by_receiver_shape() -> None:
    config = DevelopmentConfig(n_senders=5, n_receivers=7, steps=48)
    result = develop(seed=4, arm="guided", config=config)

    matrix = connectivity_matrix(result)

    assert matrix.shape == (5, 7)
    assert np.all(matrix >= 0.0)
    assert int(np.count_nonzero(matrix)) == len(result.synapses)


def test_operator_metrics_are_finite_and_stable() -> None:
    config = DevelopmentConfig(n_senders=8, n_receivers=8, steps=56)
    result = develop(seed=9, arm="guided", config=config)

    metrics = operator_metrics(result)

    for key in (
        "connection_count",
        "mean_wiring_length",
        "topographic_error",
        "effective_rank",
        "spectral_radius",
        "slow_mode_separation",
    ):
        assert math.isfinite(float(metrics[key]))
    assert 0.0 <= metrics["spectral_radius"] < 1.0
    assert len(metrics["singular_values"]) == min(config.n_senders, config.n_receivers)


def test_seed_receipt_contains_all_matched_arms() -> None:
    receipt = receipt_for_seed(seed=5, config=DevelopmentConfig(steps=44))

    assert set(receipt["arms"]) == {"guided", "shuffled_labels", "random_walk"}
    assert receipt["seed"] == 5
    assert receipt["controls"]["receptor_multiset_exact"] is True
    assert receipt["controls"]["ligand_multiset_exact"] is True
