from __future__ import annotations

import numpy as np

from growing_anttis_neuron.development import develop
from growing_anttis_neuron.physical import compile_receiver_cable, whitened_modes


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
