from __future__ import annotations

import numpy as np

from growing_anttis_neuron.development import develop
from growing_anttis_neuron.physical import (
    compile_receiver_cable,
    purification_time,
    synapse_compartment,
    synapse_physical_metrics,
    whitened_modes,
)


def _is_connected(n_nodes: int, edges: np.ndarray) -> bool:
    adjacency = {i: set() for i in range(n_nodes)}
    for left, right in np.asarray(edges, dtype=int):
        adjacency[int(left)].add(int(right))
        adjacency[int(right)].add(int(left))
    seen = {0}
    stack = [0]
    while stack:
        node = stack.pop()
        for neighbor in adjacency[node] - seen:
            seen.add(neighbor)
            stack.append(neighbor)
    return len(seen) == n_nodes


def test_receiver_cable_is_connected_positive_and_stable() -> None:
    result = develop(seed=0, arm="guided")

    for receiver in range(len(result.receivers)):
        cable = compile_receiver_cable(result, receiver)

        assert cable.positions.shape == (8, 2)
        assert cable.edges.shape == (7, 2)
        assert len({tuple(sorted(edge)) for edge in cable.edges.tolist()}) == 7
        assert _is_connected(len(cable.positions), cable.edges)
        assert np.all(np.isfinite(cable.capacitance))
        assert np.all(cable.capacitance > 0.0)
        assert np.all(np.isfinite(cable.conductance))
        assert np.all(cable.conductance > 0.0)
        np.testing.assert_allclose(cable.system_matrix, cable.system_matrix.T, rtol=0.0, atol=1e-14)
        assert np.all(np.linalg.eigvalsh(cable.system_matrix) > 0.0)
        assert np.max(np.abs(np.linalg.eigvals(cable.step_matrix))) < 1.0


def test_whitened_modes_are_sorted_orthonormal_and_positive() -> None:
    result = develop(seed=1, arm="guided")
    cable = compile_receiver_cable(result, receiver=0)

    values, vectors = whitened_modes(cable)

    assert values.shape == (8,)
    assert vectors.shape == (8, 8)
    assert np.all(np.diff(values) >= -1e-14)
    assert np.all(values > 0.0)
    np.testing.assert_allclose(vectors.T @ vectors, np.eye(8), rtol=0.0, atol=1e-12)


def test_guided_and_shuffled_have_identical_receiver_cable_physics() -> None:
    guided = develop(seed=3, arm="guided")
    shuffled = develop(seed=3, arm="shuffled_labels")

    for receiver in range(len(guided.receivers)):
        left = compile_receiver_cable(guided, receiver)
        right = compile_receiver_cable(shuffled, receiver)

        np.testing.assert_array_equal(left.positions, right.positions)
        np.testing.assert_array_equal(left.edges, right.edges)
        np.testing.assert_array_equal(left.capacitance, right.capacitance)
        np.testing.assert_array_equal(left.conductance, right.conductance)
        np.testing.assert_array_equal(left.system_matrix, right.system_matrix)
        left_values, _ = whitened_modes(left)
        right_values, _ = whitened_modes(right)
        np.testing.assert_array_equal(left_values, right_values)


def test_synapse_assignment_uses_nearest_dendrite_of_matching_receiver() -> None:
    result = develop(seed=4, arm="guided")
    assert result.synapses

    for synapse in result.synapses:
        cable = compile_receiver_cable(result, synapse.receiver)
        node = synapse_compartment(result, synapse, cable)
        assert 1 <= node < len(cable.positions)
        contact = np.array([synapse.x, synapse.y], dtype=float)
        distances = np.sum((cable.positions[1:] - contact) ** 2, axis=1)
        assert node == 1 + int(np.argmin(distances))


def test_purification_groups_degenerate_target_modes_and_reaches_threshold() -> None:
    decays = np.array([0.2, 0.2, 0.5, 0.9], dtype=float)
    energies = np.array([1.0, 3.0, 4.0, 2.0], dtype=float)

    time = purification_time(
        decays,
        energies,
        purity_target=0.95,
        degeneracy_rtol=1e-8,
        excitation_tol=1e-12,
    )

    assert time is not None
    assert time > 0.0
    slow = 4.0 * np.exp(-2.0 * 0.2 * time)
    total = slow + 4.0 * np.exp(-2.0 * 0.5 * time) + 2.0 * np.exp(-2.0 * 0.9 * time)
    assert slow / total >= 0.95 - 1e-12


def test_purification_is_invariant_to_rotation_inside_degenerate_subspace() -> None:
    decays = np.array([0.2, 0.2, 0.5, 0.9], dtype=float)
    amplitudes = np.array([1.0, np.sqrt(3.0), 2.0, np.sqrt(2.0)], dtype=float)
    theta = 0.731
    rotation = np.array(
        [[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]],
        dtype=float,
    )
    rotated = amplitudes.copy()
    rotated[:2] = rotation @ amplitudes[:2]

    first = purification_time(
        decays,
        amplitudes * amplitudes,
        purity_target=0.95,
        degeneracy_rtol=1e-8,
        excitation_tol=1e-12,
    )
    second = purification_time(
        decays,
        rotated * rotated,
        purity_target=0.95,
        degeneracy_rtol=1e-8,
        excitation_tol=1e-12,
    )

    assert first is not None and second is not None
    assert abs(first - second) < 1e-10


def test_synapse_physical_metrics_are_finite_when_nonuniform_modes_are_excited() -> None:
    result = develop(seed=5, arm="guided")
    assert result.synapses

    metrics = synapse_physical_metrics(result, result.synapses[0])

    assert metrics.compartment >= 1
    assert np.isfinite(metrics.visible_mode_effective_count)
    assert metrics.visible_mode_effective_count >= 1.0
    assert metrics.slow_target_decay is not None
    assert metrics.slow_target_decay > 0.0
    assert metrics.purification_time_95 is not None
    assert metrics.purification_time_95 >= 0.0
    assert np.isfinite(metrics.soma_transfer_resistance)
    assert metrics.soma_transfer_resistance > 0.0
