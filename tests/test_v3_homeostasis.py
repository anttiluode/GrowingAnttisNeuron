from __future__ import annotations

import numpy as np

from growing_anttis_neuron.development import develop
from growing_anttis_neuron.homeostasis import (
    HomeostaticGrowthConfig,
    grow_to_local_setpoint,
    local_voltage_rms,
)
from growing_anttis_neuron.physical import PassiveCableConfig, compile_receiver_cable, whitened_modes


def _base_world():
    result = develop(seed=0, arm="guided")
    base = compile_receiver_cable(result, receiver=0)
    return result, base


def test_equal_power_temporal_correlation_changes_local_voltage_rms() -> None:
    result, base = _base_world()
    values = [
        local_voltage_rms(
            result,
            receiver=0,
            compartment=1,
            rho=rho,
            input_variance=1.0,
            dendrite_scale=1.0,
            lineage_edges=base.edges,
        )
        for rho in (0.0, 0.2, 0.4, 0.6)
    ]

    assert all(np.isfinite(values))
    assert all(left < right for left, right in zip(values, values[1:], strict=True))


def test_fixed_lineage_growth_reduces_local_response() -> None:
    result, base = _base_world()
    small = local_voltage_rms(
        result,
        receiver=0,
        compartment=1,
        rho=0.4,
        input_variance=1.0,
        dendrite_scale=0.8,
        lineage_edges=base.edges,
    )
    large = local_voltage_rms(
        result,
        receiver=0,
        compartment=1,
        rho=0.4,
        input_variance=1.0,
        dendrite_scale=1.8,
        lineage_edges=base.edges,
    )

    assert large < small


def test_one_local_homeostat_differentiates_identical_starting_dendrites() -> None:
    result, base = _base_world()
    target = local_voltage_rms(
        result,
        receiver=0,
        compartment=1,
        rho=0.0,
        input_variance=1.0,
        dendrite_scale=1.0,
        lineage_edges=base.edges,
    )
    config = HomeostaticGrowthConfig(
        growth_rate=0.25,
        min_scale=0.5,
        max_scale=4.0,
        relative_tolerance=1e-4,
        max_steps=200,
    )
    correlations = (0.0, 0.2, 0.4, 0.6)
    grown = [
        grow_to_local_setpoint(
            result,
            receiver=0,
            compartment=1,
            rho=rho,
            target_rms=target,
            input_variance=1.0,
            initial_scale=1.0,
            lineage_edges=base.edges,
            config=config,
        )
        for rho in correlations
    ]

    assert all(item.converged for item in grown)
    scales = [item.final_scale for item in grown]
    assert abs(scales[0] - 1.0) < 1e-12
    assert all(left < right for left, right in zip(scales, scales[1:], strict=True))
    assert max(abs(item.final_rms / target - 1.0) for item in grown) <= config.relative_tolerance

    spectra = []
    for item in grown:
        cable = compile_receiver_cable(
            result,
            receiver=0,
            config=PassiveCableConfig(dendrite_scale=item.final_scale),
            lineage_edges=base.edges,
        )
        spectra.append(whitened_modes(cable)[0])
    assert not np.allclose(spectra[0], spectra[-1], rtol=1e-6, atol=1e-9)
